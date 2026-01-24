import json
import logging

from django.db import models, transaction
from django.db.models import Q, Exists, OuterRef
from django.utils import timezone
from opentelemetry import trace
from common.models import BaseModel
from datetime import timedelta
from common.constants import PhaseStatus, PhaseType, GameStatus
from adjudication.service import resolve
from order.models import OrderResolution, Order
from phase.utils import transform_options
from province.models import Province
from supply_center.models import SupplyCenter
from unit.models import Unit
from victory.utils import check_for_solo_winner
from victory.models import Victory

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class PhaseQuerySet(models.QuerySet):
    def with_detail_data(self):
        return self.prefetch_related(
            "units__nation",
            "units__province__parent",
            "units__province__named_coasts",
            "supply_centers__nation",
            "supply_centers__province__parent",
            "supply_centers__province__named_coasts",
        )

    def with_adjudication_data(self):
        return self.select_related("variant", "game").prefetch_related(
            "supply_centers__province",
            "supply_centers__nation",
            "units__province",
            "units__nation",
            "units__dislodged_by__province",
            "phase_states__member__nation",
            "phase_states__orders__source",
            "phase_states__orders__target",
            "phase_states__orders__aux",
            "phase_states__orders__named_coast",
            "phase_states__orders__resolution",
        )

    def filter_due_phases(self):
        return self.filter(
            Q(status=PhaseStatus.ACTIVE)
            & Q(game__sandbox=False)
            & (
                (Q(scheduled_resolution__isnull=False) & Q(scheduled_resolution__lte=timezone.now()))
                | ~Exists(
                    PhaseState.objects.filter(phase=OuterRef("pk"), has_possible_orders=True, orders_confirmed=False)
                )
            )
        )


class PhaseManager(models.Manager):
    def get_queryset(self):
        return PhaseQuerySet(self.model, using=self._db)

    def with_detail_data(self):
        return self.get_queryset().with_detail_data()

    def with_adjudication_data(self):
        return self.get_queryset().with_adjudication_data()

    def filter_due_phases(self):
        return self.get_queryset().filter_due_phases()

    def resolve_phase(self, phase):
        with tracer.start_as_current_span("phase.manager.resolve_phase") as span:
            span.set_attribute("phase.id", phase.id)
            span.set_attribute("game.id", str(phase.game.id))
            logger.info(f"Manually resolving phase {phase.id} ({phase.name}) for game {phase.game.id}")
            self.resolve(phase)
            logger.info(f"Successfully resolved phase {phase.id}")

    def get_phases_to_resolve(self):
        with tracer.start_as_current_span("phase.manager.get_phases_to_resolve") as span:
            logger.info("Querying phases to resolve")

            with tracer.start_as_current_span("phase.query_due_phases") as query_span:
                phases_to_resolve = list(self.filter_due_phases().with_adjudication_data())
                query_span.set_attribute("phases.found", len(phases_to_resolve))
                logger.info(f"Found {len(phases_to_resolve)} phases to resolve")

            span.set_attribute("phases.to_resolve", len(phases_to_resolve))
            logger.info(f"Identified {len(phases_to_resolve)} phases to resolve")

            return phases_to_resolve

    def resolve_due_phases(self):
        with tracer.start_as_current_span("phase.manager.resolve_due_phases") as span:
            logger.info("Starting resolution of due phases")

            phases_to_resolve = self.get_phases_to_resolve()
            total_phases_to_resolve = len(phases_to_resolve)

            resolved_count = 0
            failed_count = 0

            for phase in phases_to_resolve:
                logger.info(f"Resolving phase {phase.id} ({phase.name}) for game {phase.game.id}")
                try:
                    self.resolve(phase)
                    resolved_count += 1
                    logger.info(f"Successfully resolved phase {phase.id}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to resolve phase {phase.id} ({phase.name}): {e}", exc_info=True)

            result = {
                "resolved": resolved_count,
                "failed": failed_count,
            }

            span.set_attribute("phases.total", total_phases_to_resolve)
            span.set_attribute("phases.resolved", resolved_count)
            span.set_attribute("phases.failed", failed_count)

            logger.info(
                f"Phase resolution complete: {resolved_count} resolved, {failed_count} failed out of {total_phases_to_resolve} phases"
            )
            return result

    def resolve(self, phase):
        with tracer.start_as_current_span("phase.manager.resolve") as span:
            span.set_attribute("phase.id", phase.id)
            span.set_attribute("game.id", str(phase.game.id))
            adjudication_data = resolve(phase)

            with tracer.start_as_current_span("phase.transaction_atomic"):
                with transaction.atomic():
                    new_phase = self.create_from_adjudication_data(phase, adjudication_data)

                    victory = Victory.objects.try_create_victory(new_phase)

                    if victory:
                        new_phase.game.status = GameStatus.COMPLETED
                        new_phase.game.save()

                        new_phase.status = PhaseStatus.COMPLETED
                        new_phase.scheduled_resolution = None
                        new_phase.save()

    def create_from_adjudication_data(self, previous_phase, adjudication_data):
        with tracer.start_as_current_span("phase.create_from_adjudication_data") as span:
            span.set_attribute("previous_phase.id", previous_phase.id)
            span.set_attribute("new_phase.ordinal", previous_phase.ordinal + 1)

            if previous_phase.game.status == GameStatus.COMPLETED:
                logger.warning(f"Skipping phase creation - game {previous_phase.game.id} is already completed")
                return previous_phase

            logger.info(
                f"Creating new phase from adjudication data for previous phase {previous_phase.id} ({previous_phase.name})"
            )
            logger.debug(f"Adjudication data keys: {list(adjudication_data.keys())}")

            try:
                # Build lookup dictionaries once to avoid N+1 queries
                variant = previous_phase.variant
                province_lookup = {p.province_id: p for p in variant.provinces.all()}
                nation_lookup = {n.name: n for n in variant.nations.all()}

                # Process order resolutions
                with tracer.start_as_current_span("phase.create_order_resolutions") as resolutions_span:
                    order_count = len(previous_phase.all_orders)

                    # Delete existing resolutions in bulk
                    order_ids = [order.id for order in previous_phase.all_orders]
                    OrderResolution.objects.filter(order_id__in=order_ids).delete()

                    # Build list of resolutions to bulk create
                    resolutions_to_create = []
                    for order in previous_phase.all_orders:
                        resolution_data = next(
                            (r for r in adjudication_data["resolutions"] if r["province"] == order.source.province_id),
                            None,
                        )
                        if resolution_data:
                            by_province = province_lookup.get(resolution_data["by"]) if resolution_data["by"] else None
                            resolutions_to_create.append(
                                OrderResolution(
                                    order=order,
                                    status=resolution_data["result"],
                                    by=by_province,
                                )
                            )
                            logger.debug(f"Prepared resolution for order {order.id}: {resolution_data['result']}")
                        else:
                            logger.warning(
                                f"No resolution found for order {order.id} in province {order.source.province_id}"
                            )

                    # Bulk create all resolutions
                    OrderResolution.objects.bulk_create(resolutions_to_create)
                    resolutions_count = len(resolutions_to_create)

                    resolutions_span.set_attribute("order_count", order_count)
                    resolutions_span.set_attribute("resolutions_created", resolutions_count)
                    logger.info(f"Created {resolutions_count} order resolutions")

                # Calculate next phase details
                phase_duration_seconds = previous_phase.game.movement_phase_duration_seconds
                scheduled_resolution = (
                    timezone.now() + timedelta(seconds=phase_duration_seconds) if phase_duration_seconds else None
                )
                new_ordinal = previous_phase.ordinal + 1

                logger.info(
                    f"Creating new phase {new_ordinal} ({adjudication_data['season']} {adjudication_data['year']}, {adjudication_data['type']})"
                )

                # Create the new phase
                with tracer.start_as_current_span("phase.create_new_phase") as new_phase_span:
                    new_phase = self.create(
                        game=previous_phase.game,
                        variant=previous_phase.variant,
                        ordinal=new_ordinal,
                        season=adjudication_data["season"],
                        year=adjudication_data["year"],
                        type=adjudication_data["type"],
                        options=adjudication_data["options"],
                        status=PhaseStatus.ACTIVE,
                        scheduled_resolution=scheduled_resolution,
                    )
                    new_phase_span.set_attribute("phase.id", new_phase.id)
                    new_phase_span.set_attribute("phase.ordinal", new_ordinal)
                    new_phase_span.set_attribute("phase.season", adjudication_data["season"])
                    new_phase_span.set_attribute("phase.year", adjudication_data["year"])
                    new_phase_span.set_attribute("phase.type", adjudication_data["type"])

                logger.info(f"Created new phase {new_phase.id} scheduled for resolution at {scheduled_resolution}")

                # Create supply centers
                with tracer.start_as_current_span("phase.create_supply_centers") as sc_span:
                    supply_centers_to_create = []
                    for supply_center in adjudication_data["supply_centers"]:
                        province = province_lookup.get(supply_center["province"])
                        nation = nation_lookup.get(supply_center["nation"])
                        if province and nation:
                            supply_centers_to_create.append(
                                SupplyCenter(
                                    province=province,
                                    nation=nation,
                                    phase=new_phase,
                                )
                            )
                        else:
                            logger.error(
                                f"Failed to find province {supply_center['province']} or nation {supply_center['nation']}"
                            )

                    # Bulk create all supply centers
                    SupplyCenter.objects.bulk_create(supply_centers_to_create)
                    supply_centers_count = len(supply_centers_to_create)

                    sc_span.set_attribute("supply_centers_count", supply_centers_count)
                    logger.info(f"Created {supply_centers_count} supply centers")

                # Create units
                with tracer.start_as_current_span("phase.create_units") as units_span:
                    # Build a lookup for previous phase units by province_id to avoid N+1 queries
                    previous_units_by_province = {
                        u.province.province_id: u for u in previous_phase.units.select_related("province").all()
                    }

                    units_to_create = []
                    for unit in adjudication_data["units"]:
                        logger.info(
                            f"Preparing unit {unit['type']} for nation {unit['nation']} in province {unit['province']}"
                        )

                        is_dislodged = unit.get("dislodged", False)

                        dislodged_by_id = unit.get("dislodged_by", None)
                        dislodged_by_unit = None

                        if is_dislodged and dislodged_by_id:
                            dislodged_by_unit = previous_units_by_province.get(dislodged_by_id)
                            if not dislodged_by_unit:
                                logger.warning(
                                    f"Unit {unit['province']} is dislodged but dislodger {dislodged_by_id} not found in previous phase"
                                )
                        elif is_dislodged:
                            logger.info(
                                f"Unit {unit['province']} is dislodged but no dislodger information available (convoy case)"
                            )

                        province = province_lookup.get(unit["province"])
                        nation = nation_lookup.get(unit["nation"])
                        if province and nation:
                            units_to_create.append(
                                Unit(
                                    type=unit["type"],
                                    nation=nation,
                                    province=province,
                                    phase=new_phase,
                                    dislodged=is_dislodged,
                                    dislodged_by=dislodged_by_unit,
                                )
                            )
                        else:
                            logger.error(f"Failed to find province {unit['province']} or nation {unit['nation']}")

                    # Bulk create all units
                    Unit.objects.bulk_create(units_to_create)
                    units_count = len(units_to_create)

                    units_span.set_attribute("units_count", units_count)
                    logger.info(f"Created {units_count} units")

                # Create phase states
                with tracer.start_as_current_span("phase.create_phase_states") as ps_span:
                    nations_with_orders = new_phase.nations_with_possible_orders

                    # Prefetch member nations to avoid N+1
                    members = list(new_phase.game.members.select_related("nation").all())

                    phase_states_to_create = []
                    for member in members:
                        phase_states_to_create.append(
                            new_phase.phase_states.model(
                                member=member,
                                phase=new_phase,
                                has_possible_orders=member.nation.name in nations_with_orders,
                            )
                        )

                    # Bulk create all phase states
                    new_phase.phase_states.model.objects.bulk_create(phase_states_to_create)
                    phase_states_count = len(phase_states_to_create)

                    ps_span.set_attribute("phase_states_count", phase_states_count)
                    logger.info(f"Created {phase_states_count} phase states for game members")

                # Mark previous phase as completed
                with tracer.start_as_current_span("phase.mark_previous_complete") as complete_span:
                    complete_span.set_attribute("previous_phase.id", previous_phase.id)
                    previous_phase.status = PhaseStatus.COMPLETED
                    previous_phase.save()
                    logger.info(f"Marked previous phase {previous_phase.id} as completed")

                logger.info(f"Successfully created new phase {new_phase.id} from adjudication data")
                return new_phase

            except Exception as e:
                logger.error(
                    f"Failed to create phase from adjudication data for phase {previous_phase.id}: {e}", exc_info=True
                )
                raise


class Phase(BaseModel):

    objects = PhaseManager()

    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="phases", null=True, blank=True)
    variant = models.ForeignKey(
        "variant.Variant", on_delete=models.CASCADE, related_name="phases", null=True, blank=True
    )
    ordinal = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=20, choices=PhaseStatus.STATUS_CHOICES, default=PhaseStatus.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    season = models.CharField(max_length=10)
    year = models.IntegerField()
    type = models.CharField(max_length=10)
    scheduled_resolution = models.DateTimeField(null=True, blank=True)
    options = models.JSONField(default=dict)

    class Meta:
        ordering = ["ordinal"]

    def __str__(self):
        return f"{self.name} ({self.game.name if self.game else '-'})"

    @property
    def name(self):
        return f"{self.season} {self.year}, {self.type}"

    @property
    def remaining_time(self):
        if self.scheduled_resolution and self.status == PhaseStatus.ACTIVE:
            delta = self.scheduled_resolution - timezone.now()
            return max(delta, timedelta(seconds=0))
        return None

    @property
    def remaining_time_seconds(self):
        if self.remaining_time:
            return self.remaining_time.total_seconds()
        return None

    @property
    def all_orders(self):
        return [order for phase_state in self.phase_states.all() for order in phase_state.orders.all()]

    @property
    def transformed_options(self):
        return transform_options(self.options or {})

    @property
    def nations_with_possible_orders(self):
        nations = set()
        for nation, options in (self.transformed_options or {}).items():
            if any(province_data for province_data in options.values()):
                nations.add(nation)
        return nations

    @property
    def phase_states_with_possible_orders(self):
        nations = self.nations_with_possible_orders
        logger.info(f"Nations with possible orders: {nations}")
        return [phase_state for phase_state in self.phase_states.all() if phase_state.member.nation.name in nations]

    @property
    def should_resolve_immediately(self):
        logger.info(f"Checking if phase {self.id} should resolve immediately")
        return all(phase_state.orders_confirmed for phase_state in self.phase_states_with_possible_orders)

    @property
    def previous_phase_id(self):
        if not self.game:
            return None
        return (
            Phase.objects.filter(game=self.game, ordinal__lt=self.ordinal)
            .order_by("-ordinal")
            .values_list("id", flat=True)
            .first()
        )

    @property
    def next_phase_id(self):
        if not self.game:
            return None
        return (
            Phase.objects.filter(game=self.game, ordinal__gt=self.ordinal)
            .order_by("ordinal")
            .values_list("id", flat=True)
            .first()
        )

    def revert_to_this_phase(self):

        logger.info(f"Reverting game {self.game.id} to phase {self.id} ({self.name})")

        if self.game.status == GameStatus.COMPLETED:
            logger.error(f"Cannot revert phase {self.id} - game {self.game.id} has ended")
            raise ValueError("Cannot revert phases in an ended game")

        later_phases = self.game.phases.filter(ordinal__gt=self.ordinal)
        later_phases_count = later_phases.count()
        logger.info(f"Deleting {later_phases_count} phases after phase {self.ordinal}")
        later_phases.delete()

        orders_count = Order.objects.filter(phase_state__phase=self).count()
        logger.info(f"Deleting {orders_count} orders for phase {self.id}")
        Order.objects.filter(phase_state__phase=self).delete()

        logger.info(f"Reactivating phase {self.id} with new scheduled resolution")
        self.status = PhaseStatus.ACTIVE
        phase_duration_seconds = self.game.movement_phase_duration_seconds
        self.scheduled_resolution = timezone.now() + timedelta(seconds=phase_duration_seconds)
        self.save()

        phase_states_count = self.phase_states.count()
        logger.info(f"Resetting orders_confirmed to False for {phase_states_count} phase states")
        self.phase_states.update(orders_confirmed=False)

        logger.info(f"Successfully reverted game {self.game.id} to phase {self.id}")


class PhaseState(BaseModel):
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="phase_states")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="phase_states")
    orders_confirmed = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    has_possible_orders = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member.user.username} - {self.phase.name}"

    def max_allowed_adjustment_orders(self):
        if self.phase.type != PhaseType.ADJUSTMENT:
            return float("inf")

        nation = self.member.nation
        supply_centers_count = self.phase.supply_centers.filter(nation=nation).count()
        units_count = self.phase.units.filter(nation=nation).count()
        return abs(supply_centers_count - units_count)

    def get_orderable_provinces(self, provinces):

        options = self.phase.transformed_options
        nation = self.member.nation
        orderable_ids = list(options[nation.name].keys())

        if isinstance(provinces, dict):
            province_ids = [p.id for p in provinces.values() if p.province_id in orderable_ids]
            base_provinces = Province.objects.filter(id__in=province_ids)
        else:
            base_provinces = provinces.filter(province_id__in=orderable_ids)

        base_provinces = base_provinces.select_related("parent").prefetch_related("named_coasts")

        if self.phase.type == PhaseType.ADJUSTMENT:
            max_orders = self.max_allowed_adjustment_orders()
            current_orders = self.orders.count()

            if current_orders >= max_orders:
                provinces_with_orders = self.orders.values_list("source__province_id", flat=True)
                return base_provinces.filter(province_id__in=provinces_with_orders)

        return base_provinces

    @property
    def orderable_provinces(self):
        provinces = self.phase.variant.provinces.all()
        return self.get_orderable_provinces(provinces)
