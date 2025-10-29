import json
import logging

from django.db import models
from django.utils import timezone
from common.models import BaseModel
from datetime import timedelta
from common.constants import PhaseStatus, PhaseType, GameStatus
from adjudication.service import resolve
from order.models import OrderResolution, Order
from phase.utils import transform_options

logger = logging.getLogger(__name__)


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


class PhaseManager(models.Manager):
    def get_queryset(self):
        return PhaseQuerySet(self.model, using=self._db)

    def with_detail_data(self):
        return self.get_queryset().with_detail_data()

    def resolve_phase(self, phase):
        logger.info(f"Manually resolving phase {phase.id} ({phase.name}) for game {phase.game.id}")
        self.resolve(phase)
        logger.info(f"Successfully resolved phase {phase.id}")

    def resolve_due_phases(self):
        logger.info("Starting resolution of due phases")

        phases = self.get_queryset().filter(status=PhaseStatus.ACTIVE)
        total_phases = phases.count()
        logger.info(f"Found {total_phases} active phases to check for resolution")

        resolved_count = 0
        failed_count = 0

        for phase in phases:
            if phase.scheduled_resolution is None:
                logger.debug(f"Phase {phase.id} ({phase.name}) has no scheduled resolution (sandbox game), skipping")
                continue

            should_resolve = (phase.scheduled_resolution <= timezone.now()) or phase.should_resolve_immediately

            if should_resolve:
                logger.info(f"Resolving phase {phase.id} ({phase.name}) for game {phase.game.id}")
                try:
                    self.resolve(phase)
                    resolved_count += 1
                    logger.info(f"Successfully resolved phase {phase.id}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to resolve phase {phase.id} ({phase.name}): {e}", exc_info=True)
            else:
                logger.debug(f"Phase {phase.id} ({phase.name}) not due for resolution yet")

        result = {
            "resolved": resolved_count,
            "failed": failed_count,
        }

        logger.info(
            f"Phase resolution complete: {resolved_count} resolved, {failed_count} failed out of {total_phases} total phases"
        )
        return result

    def resolve(self, phase):
        adjudication_data = resolve(phase)
        self.create_from_adjudication_data(phase, adjudication_data)

    def create_from_adjudication_data(self, previous_phase, adjudication_data):
        logger.info(
            f"Creating new phase from adjudication data for previous phase {previous_phase.id} ({previous_phase.name})"
        )
        logger.debug(f"Adjudication data keys: {list(adjudication_data.keys())}")

        try:
            # Process order resolutions
            resolutions_count = 0
            for order in previous_phase.all_orders:
                resolution = next(
                    (r for r in adjudication_data["resolutions"] if r["province"] == order.source.province_id), None
                )
                if resolution:
                    if hasattr(order, "resolution"):
                        order.resolution.delete()
                    by_province = (
                        previous_phase.variant.provinces.get(province_id=resolution["by"]) if resolution["by"] else None
                    )
                    OrderResolution.objects.create(
                        order=order,
                        status=resolution["result"],
                        by=by_province,
                    )
                    resolutions_count += 1
                    logger.debug(f"Created resolution for order {order.id}: {resolution['result']}")
                else:
                    logger.warning(f"No resolution found for order {order.id} in province {order.source.province_id}")

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

            logger.info(f"Created new phase {new_phase.id} scheduled for resolution at {scheduled_resolution}")

            # Create supply centers
            supply_centers_count = 0
            for supply_center in adjudication_data["supply_centers"]:
                try:
                    new_phase.supply_centers.create(
                        province=new_phase.variant.provinces.get(province_id=supply_center["province"]),
                        nation=new_phase.variant.nations.get(name=supply_center["nation"]),
                    )
                    supply_centers_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to create supply center for province {supply_center['province']}, nation {supply_center['nation']}: {e}"
                    )

            logger.info(f"Created {supply_centers_count} supply centers")

            # Create units
            units_count = 0
            for unit in adjudication_data["units"]:
                try:
                    logger.info(
                        f"Creating unit {unit['type']} for nation {unit['nation']} in province {unit['province']}"
                    )
                    dislodged_by_id = unit.get("dislodged_by", None)
                    logger.info(f"Dislodged by ID: {dislodged_by_id}")
                    dislodged_by = (
                        previous_phase.units.filter(province__province_id=dislodged_by_id).first()
                        if dislodged_by_id
                        else None
                    )
                    logger.info(f"Dislodged by: {dislodged_by}")
                    new_phase.units.create(
                        type=unit["type"],
                        nation=new_phase.variant.nations.get(name=unit["nation"]),
                        province=new_phase.variant.provinces.get(province_id=unit["province"]),
                        dislodged_by=dislodged_by,
                    )
                    units_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to create unit {unit['type']} for nation {unit['nation']} in province {unit['province']}: {e}"
                    )

            logger.info(f"Created {units_count} units")

            # Create phase states
            phase_states_count = 0
            for member in new_phase.game.members.all():
                new_phase.phase_states.create(
                    member=member,
                )
                phase_states_count += 1

            logger.info(f"Created {phase_states_count} phase states for game members")

            # Mark previous phase as completed
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

    def __str__(self):
        return f"{self.member.user.username} - {self.phase.name}"

    def max_allowed_adjustment_orders(self):
        if self.phase.type != PhaseType.ADJUSTMENT:
            return float("inf")

        nation = self.member.nation
        supply_centers_count = self.phase.supply_centers.filter(nation=nation).count()
        units_count = self.phase.units.filter(nation=nation).count()
        return abs(supply_centers_count - units_count)

    @property
    def orderable_provinces(self):
        options = self.phase.transformed_options
        nation = self.member.nation
        orderable_ids = list(options[nation.name].keys())
        base_provinces = (
            self.phase.variant.provinces.select_related("parent")
            .prefetch_related("named_coasts")
            .filter(province_id__in=orderable_ids)
        )

        if self.phase.type == PhaseType.ADJUSTMENT:
            max_orders = self.max_allowed_adjustment_orders()
            current_orders = self.orders.count()

            if current_orders >= max_orders:
                # At limit: only show provinces with existing orders (for editing)
                provinces_with_orders = self.orders.values_list("source__province_id", flat=True)
                return base_provinces.filter(province_id__in=provinces_with_orders)

        return base_provinces
