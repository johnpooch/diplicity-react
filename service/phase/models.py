import json
from contextlib import contextmanager
from functools import cached_property

from django.db import models, transaction
from django.db.models import F, Q, Exists, OuterRef, Count, Prefetch
from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app
from common.models import BaseModel
from datetime import timedelta
from common.constants import PhaseStatus, PhaseType, GameStatus, DeadlineMode, OrderType, UserKind, ResolutionJob
from adjudicator.service import resolve
from member.models import Member
from order.models import OrderResolution, Order
from phase.utils import transform_options, format_time_remaining, build_notification_body, compress_deadline, format_deadline, count_actionable_units
from province.models import Province
from supply_center.models import SupplyCenter
from unit.models import Unit
from victory.utils import check_for_solo_winner
from victory.models import Victory
from emit import emit


class PhaseQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("variant", "game").prefetch_related(
            "units__nation__flag",
            "units__province__parent",
            "units__province__named_coasts",
            "units__dislodged_from__parent",
            "supply_centers__nation__flag",
            "supply_centers__province__parent",
            "supply_centers__province__named_coasts",
            "variant__provinces__parent",
            "variant__nations",
            "phase_states__member__nation__flag",
            "phase_states__orders__source",
            "phase_states__orders__target",
            "phase_states__orders__aux",
            "phase_states__orders__named_coast",
            "phase_states__orders__resolution",
        )

    def filter_armable(self):
        return self.filter(
            Q(status=PhaseStatus.ACTIVE)
            & Q(game__sandbox=False)
            & Q(game__paused_at__isnull=True)
            & ~Q(game__status=GameStatus.COMPLETED)
            & ~Q(game__status=GameStatus.ABANDONED)
        )

    def filter_due_phases(self):
        deadline_passed = (
            Q(scheduled_resolution__isnull=False)
            & Q(scheduled_resolution__lte=timezone.now())
        )
        all_confirmed = ~Exists(
            PhaseState.objects.filter(phase=OuterRef("pk"), has_possible_orders=True, orders_confirmed=False)
        )
        return self.filter_armable().filter(deadline_passed | all_confirmed)


class PhaseManager(models.Manager):
    def get_queryset(self):
        return PhaseQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def filter_armable(self):
        return self.get_queryset().filter_armable()

    def filter_due_phases(self):
        return self.get_queryset().filter_due_phases()

    def lock_if_active(self, phase_id):
        return (
            self.defer("options")
            .select_for_update()
            .filter(pk=phase_id, status=PhaseStatus.ACTIVE)
            .first()
        )

    @contextmanager
    def claim(self, phase_id, queryset):
        claimed = queryset.filter(pk=phase_id).update(
            status=PhaseStatus.PROCESSING, processing_started_at=timezone.now()
        )
        try:
            yield bool(claimed)
        except Exception:
            if claimed:
                self.release_from_processing(phase_id)
            raise

    def release_from_processing(self, phase_id):
        return self.filter(pk=phase_id, status=PhaseStatus.PROCESSING).update(
            status=PhaseStatus.ACTIVE, processing_started_at=None
        )

    def arm_resolution(self, phase, not_before=None):
        state = list(
            self.filter(pk=phase.pk)
            .annotate(armable=Exists(self.filter_armable().filter(pk=OuterRef("pk"))))
            .values_list("resolution_job_id", "scheduled_resolution", "armable")[:1]
        )
        if not state:
            return None
        current_job_id, scheduled_resolution, armable = state[0]

        should_arm, schedule_at = self._resolution_schedule(
            phase, scheduled_resolution, armable, not_before
        )

        if current_job_id is not None:
            armed = procrastinate_app.job_manager.list_jobs(id=current_job_id)
            if (
                should_arm
                and armed
                and armed[0].status == ResolutionJob.TODO
                and armed[0].scheduled_at == schedule_at
            ):
                return current_job_id
            procrastinate_app.job_manager.cancel_job_by_id(current_job_id)

        new_job_id = None
        if should_arm:
            new_job_id = procrastinate_app.configure_task(
                ResolutionJob.TASK_NAME,
                schedule_at=schedule_at,
                lock=ResolutionJob.lock_for_game(phase.game_id),
            ).defer(phase_id=phase.pk)

        if new_job_id != current_job_id:
            self.filter(pk=phase.pk).update(resolution_job_id=new_job_id)
            phase.resolution_job_id = new_job_id

        return new_job_id

    def _resolution_schedule(self, phase, scheduled_resolution, armable, not_before):
        if not armable:
            return False, None

        if self._is_resolvable(phase):
            return True, not_before

        if scheduled_resolution is None:
            return False, None

        if not_before is not None and not_before > scheduled_resolution:
            return True, not_before

        return True, scheduled_resolution

    def _is_resolvable(self, phase):
        states = list(
            PhaseState.objects.filter(phase_id=phase.pk).values_list(
                "has_possible_orders", "orders_confirmed"
            )
        )
        if not states:
            return False
        return all(confirmed for has_possible_orders, confirmed in states if has_possible_orders)

    def backfill_resolution_jobs(self):
        armed = 0
        for phase in self.filter_armable().iterator():
            previous_job_id = phase.resolution_job_id
            if self.arm_resolution(phase) != previous_job_id:
                armed += 1
        return armed

    def resolve_if_due(self, phase_id):
        with self.claim(phase_id, self.filter_due_phases()) as claimed:
            if not claimed:
                return None
            phase = self.with_related_data().get(pk=phase_id)
            if self._apply_nmr_extensions(phase):
                return None
            return self._resolve_claimed(phase)

    def _apply_nmr_extensions(self, phase):
        not_submitted = phase.phase_states.filter(
            has_possible_orders=True
        ).exclude(
            member__civil_disorder=True
        ).annotate(order_count=Count("orders")).filter(order_count=0).select_related('member')

        candidates = [ps for ps in not_submitted if ps.member.nmr_extensions_remaining > 0]
        if not candidates:
            return None

        actionable_units = count_actionable_units(
            phase.type, phase.units.all(), phase.supply_centers.all()
        )

        members_with_extensions = [
            ps.member for ps in candidates
            if actionable_units.get(ps.member.nation_id, 0) > 0
        ]

        if not members_with_extensions:
            return None

        new_resolution = phase.game.get_scheduled_resolution(phase.type)
        if not new_resolution:
            return None

        phase.scheduled_resolution = new_resolution
        phase.status = PhaseStatus.ACTIVE
        phase.processing_started_at = None
        phase.save()

        for member in members_with_extensions:
            member.nmr_extensions_remaining -= 1
        Member.objects.bulk_update(members_with_extensions, ['nmr_extensions_remaining'])

        for member in members_with_extensions:
            if member.user_id is None:
                continue
            emit("nmr_extension_used", phase=phase, actor=member.user)

        emit("nmr_extension_applied", phase=phase)

        return members_with_extensions

    def send_deadline_warnings(self):
        WARNING_THRESHOLDS = {
            3600: 900,
            12 * 3600: 3600,
            24 * 3600: 3600,
            48 * 3600: 7200,
            72 * 3600: 7200,
            96 * 3600: 7200,
            168 * 3600: 14400,
            336 * 3600: 14400,
        }

        def get_warning_threshold(duration_seconds):
            if not duration_seconds:
                return 3600
            for phase_duration, warning in sorted(WARNING_THRESHOLDS.items()):
                if duration_seconds <= phase_duration:
                    return warning
            return 14400

        now = timezone.now()

        active_phases = self.filter(
            status=PhaseStatus.ACTIVE,
            game__sandbox=False,
            game__paused_at__isnull=True,
            scheduled_resolution__isnull=False,
        ).exclude(
            Q(game__status=GameStatus.COMPLETED) | Q(game__status=GameStatus.ABANDONED)
        ).select_related('game').prefetch_related(
            'phase_states__member__user',
            'phase_states__member__nation',
            'phase_states__orders',
            Prefetch('units', queryset=Unit.objects.select_related('nation'), to_attr='prefetched_units'),
            Prefetch('supply_centers', queryset=SupplyCenter.objects.select_related('nation'), to_attr='prefetched_supply_centers'),
        )

        notifications_sent = 0

        for phase in active_phases:
            duration_seconds = phase.game.get_effective_phase_duration_seconds(phase.type)
            warning_threshold = get_warning_threshold(duration_seconds)
            time_until_deadline = (phase.scheduled_resolution - now).total_seconds()

            if time_until_deadline <= 0 or time_until_deadline > warning_threshold:
                continue

            is_fixed_time = phase.game.deadline_mode == DeadlineMode.FIXED_TIME
            time_left = format_time_remaining(time_until_deadline)

            actionable_units = count_actionable_units(
                phase.type, phase.prefetched_units, phase.prefetched_supply_centers
            )

            is_adjustment = phase.type == PhaseType.ADJUSTMENT
            warned_states = []

            for ps in phase.phase_states.all():
                if not ps.has_possible_orders:
                    continue
                if ps.deadline_warning_sent_for == phase.scheduled_resolution:
                    continue

                total_units = actionable_units.get(ps.member.nation_id, 0)

                if total_units == 0:
                    continue

                body = build_notification_body(
                    ps.orders_confirmed, is_fixed_time, len(ps.orders.all()), total_units, time_left,
                    ps.member.nmr_extensions_remaining,
                    is_adjustment=is_adjustment,
                )
                if body is None:
                    continue

                if ps.member.user_id is None:
                    continue

                emit("deadline_warning", game=phase.game, recipients=[ps.member.user_id], body=body)
                ps.deadline_warning_sent_for = phase.scheduled_resolution
                warned_states.append(ps)
                notifications_sent += 1

            if warned_states:
                PhaseState.objects.bulk_update(warned_states, ["deadline_warning_sent_for"])

        return {"notifications_sent": notifications_sent}

    def _set_orders_outcome(self, phase):
        base_qs = phase.phase_states.filter(
            has_possible_orders=True
        ).annotate(order_count=Count("orders"))

        received_ids = list(base_qs.filter(order_count__gt=0).values_list("id", flat=True))
        nmr_ids = list(base_qs.filter(order_count=0).values_list("id", flat=True))

        if received_ids:
            PhaseState.objects.filter(id__in=received_ids).update(
                orders_outcome=PhaseState.OrdersOutcome.RECEIVED
            )
        if nmr_ids:
            PhaseState.objects.filter(id__in=nmr_ids).update(
                orders_outcome=PhaseState.OrdersOutcome.NMR
            )

    def _check_civil_disorder(self, phase):
        if phase.game.sandbox:
            return []
        if phase.type != PhaseType.MOVEMENT:
            return []

        current_nmr_members = []
        for phase_state in phase.phase_states.select_related("member").all():
            if phase_state.orders_outcome != PhaseState.OrdersOutcome.NMR:
                continue
            member = phase_state.member
            if member.civil_disorder or member.eliminated or member.kicked:
                continue
            current_nmr_members.append(member)

        if not current_nmr_members:
            return []

        prev_movement_states = (
            PhaseState.objects.filter(
                member__in=current_nmr_members,
                phase__game=phase.game,
                phase__type=PhaseType.MOVEMENT,
                phase__status=PhaseStatus.COMPLETED,
                phase__ordinal__lt=phase.ordinal,
                has_possible_orders=True,
            )
            .order_by("member_id", "-phase__ordinal")
        )

        latest_prev_by_member = {}
        for ps in prev_movement_states:
            if ps.member_id not in latest_prev_by_member:
                latest_prev_by_member[ps.member_id] = ps

        newly_cd_members = [
            m for m in current_nmr_members
            if m.id in latest_prev_by_member
            and latest_prev_by_member[m.id].orders_outcome == PhaseState.OrdersOutcome.NMR
        ]

        if not newly_cd_members:
            return []

        for m in newly_cd_members:
            m.civil_disorder = True
        Member.objects.bulk_update(newly_cd_members, ["civil_disorder"])

        if any(m.user_id == phase.game.admin_id for m in newly_cd_members):
            phase.game.reassign_admin()

        return newly_cd_members

    def _reconcile_civil_disorder_eliminations(self, newly_cd_members, adjudication_data):
        if not newly_cd_members:
            return []

        surviving_nations = {u["nation"] for u in adjudication_data["units"]} | {
            sc["nation"] for sc in adjudication_data["supply_centers"]
        }

        eliminated = [
            m for m in newly_cd_members
            if m.nation is not None and m.nation.name not in surviving_nations
        ]
        surviving = [m for m in newly_cd_members if m not in eliminated]

        if eliminated:
            for m in eliminated:
                m.civil_disorder = False
            Member.objects.bulk_update(eliminated, ["civil_disorder"])

        return surviving

    def _recompute_commitment(self, phase):
        from user_profile.commitment import recompute_commitment

        if phase.game.sandbox or phase.game.private:
            return

        users = [
            phase_state.member.user
            for phase_state in phase.phase_states.select_related("member__user__profile")
            if phase_state.has_possible_orders and phase_state.member.user_id is not None
        ]
        for user in users:
            try:
                with transaction.atomic():
                    recompute_commitment(user)
            except Exception:
                continue

    def _notify_civil_disorder(self, phase, newly_cd_members):
        if not newly_cd_members:
            return

        cd_user_ids = [m.user_id for m in newly_cd_members if m.user_id is not None]
        self._remove_from_staging_games(cd_user_ids)

        nation_names = ", ".join(
            m.nation.name for m in newly_cd_members if m.nation is not None
        )

        emit("civil_disorder", game=phase.game, nation_names=nation_names)

    def _remove_from_staging_games(self, user_ids):
        if not user_ids:
            return

        staging_members = list(
            Member.objects.filter(
                user_id__in=user_ids,
                game__status__in=[GameStatus.PENDING, GameStatus.MUSTERING],
            )
            .exclude(game__created_by_id=F("user_id"))
            .select_related("game")
        )

        if not staging_members:
            return

        game_ids = {m.game_id for m in staging_members}

        Member.objects.filter(id__in=[m.id for m in staging_members]).delete()

        for m in staging_members:
            if m.user_id is None:
                continue
            emit("removed_from_staging", game=m.game, recipients=[m.user_id])

        from game.models import Game
        for game in Game.objects.filter(
            id__in=game_ids, status__in=[GameStatus.PENDING, GameStatus.MUSTERING]
        ):
            game.delete_if_empty_pending()

    def _check_eliminations(self, previous_phase, new_phase):
        units_by_nation = {}
        for unit in new_phase.units.all():
            units_by_nation[unit.nation_id] = units_by_nation.get(unit.nation_id, 0) + 1

        sc_by_nation = {}
        for sc in new_phase.supply_centers.all():
            sc_by_nation[sc.nation_id] = sc_by_nation.get(sc.nation_id, 0) + 1

        candidates = list(
            previous_phase.game.members.filter(
                eliminated=False, kicked=False, nation__isnull=False
            ).select_related("user", "nation")
        )

        newly_eliminated = [
            m for m in candidates
            if units_by_nation.get(m.nation_id, 0) == 0
            and sc_by_nation.get(m.nation_id, 0) == 0
        ]

        if not newly_eliminated:
            return

        for m in newly_eliminated:
            m.eliminated = True
        Member.objects.bulk_update(newly_eliminated, ["eliminated"])

        game = previous_phase.game

        for member in newly_eliminated:
            if member.user_id is None:
                continue
            emit("elimination", game=game, recipients=[member.user_id])

    def _check_abandonment(self, game):
        if game.sandbox:
            return False

        active_members = list(game.members.filter(eliminated=False, kicked=False))
        if not active_members:
            return False

        return all(m.civil_disorder for m in active_members)

    def resolve(self, phase):
        with self.claim(phase.pk, self.filter(status=PhaseStatus.ACTIVE)) as claimed:
            if not claimed:
                return phase
            phase.status = PhaseStatus.PROCESSING
            return self._resolve_claimed(phase)

    def _resolve_claimed(self, phase):
        with transaction.atomic():
            self._set_orders_outcome(phase)
            newly_cd_members = self._check_civil_disorder(phase)
            adjudication_data = resolve(phase)

            surviving_cd_members = self._reconcile_civil_disorder_eliminations(
                newly_cd_members, adjudication_data
            )
            new_phase = self.create_from_adjudication_data(phase, adjudication_data)
            self._check_eliminations(phase, new_phase)
            self._notify_civil_disorder(phase, surviving_cd_members)
            self._recompute_commitment(phase)

            victory = Victory.objects.try_create_victory(new_phase)

            if victory:
                new_phase.game.finish(GameStatus.COMPLETED)
                new_phase.game.emit_game_ended()
            elif self._check_abandonment(new_phase.game):
                new_phase.game.finish(GameStatus.ABANDONED)

            new_phase.refresh_from_db()

            if new_phase.status == PhaseStatus.ACTIVE:
                emit("phase_started", phase=new_phase)

            return new_phase

    def _emit_phase_resolved(self, phase):
        resolved_early = (
            phase.game.deadline_mode == DeadlineMode.FIXED_TIME
            and phase.scheduled_resolution is not None
            and timezone.now() < phase.scheduled_resolution
        )
        event_type = "phase_resolved_early" if resolved_early else "phase_resolved"
        emit(event_type, phase=phase)

    def create_from_adjudication_data(self, previous_phase, adjudication_data):
        if previous_phase.game.status in (GameStatus.COMPLETED, GameStatus.ABANDONED):
            return previous_phase

        # Build lookup dictionaries once to avoid N+1 queries
        variant = previous_phase.variant
        province_lookup = {p.province_id: p for p in variant.provinces.all()}
        nation_lookup = {n.name: n for n in variant.nations.all()}

        # Process order resolutions
        existing_orders = list(previous_phase.all_orders)

        order_ids = [order.id for order in existing_orders]
        OrderResolution.objects.filter(order_id__in=order_ids).delete()

        unit_nation_by_province = {
            unit.province.province_id: unit.nation
            for unit in previous_phase.units.all()
        }
        phase_state_by_nation_name = {
            ps.member.nation.name: ps
            for ps in previous_phase.phase_states.all()
        }
        existing_order_provinces = {order.source.province_id for order in existing_orders}

        implicit_orders_to_create = []
        implicit_resolution_pairs = []
        for resolution_data in adjudication_data["resolutions"]:
            if resolution_data["result"] != "OK" and resolution_data["province"] not in existing_order_provinces:
                source_province = province_lookup.get(resolution_data["province"])
                nation = unit_nation_by_province.get(resolution_data["province"])
                if source_province and nation:
                    phase_state = phase_state_by_nation_name.get(nation.name)
                    if phase_state:
                        implicit_orders_to_create.append(
                            Order(
                                phase_state=phase_state,
                                source=source_province,
                                order_type=OrderType.HOLD,
                                is_implicit=True,
                            )
                        )
                        implicit_resolution_pairs.append(resolution_data)

        resolutions_to_create = []

        if implicit_orders_to_create:
            created_implicit_orders = Order.objects.bulk_create(implicit_orders_to_create)
            for implicit_order, resolution_data in zip(created_implicit_orders, implicit_resolution_pairs):
                by_province = province_lookup.get(resolution_data["by"]) if resolution_data["by"] else None
                resolutions_to_create.append(
                    OrderResolution(
                        order=implicit_order,
                        status=resolution_data["result"],
                        by=by_province,
                    )
                )

        for order in existing_orders:
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

        OrderResolution.objects.bulk_create(resolutions_to_create)

        # Calculate next phase details
        scheduled_resolution = previous_phase.game.get_scheduled_resolution(
            adjudication_data["type"],
            reference_time=previous_phase.scheduled_resolution,
        )
        if (
            scheduled_resolution is not None
            and previous_phase.game.deadline_mode == DeadlineMode.FIXED_TIME
        ):
            scheduled_resolution = compress_deadline(
                scheduled_resolution,
                previous_phase.game.get_phase_frequency(adjudication_data["type"]),
                timezone.now(),
            )
        new_ordinal = previous_phase.ordinal + 1

        # Create the new phase
        new_phase = self.create(
            game=previous_phase.game,
            variant=previous_phase.variant,
            ordinal=new_ordinal,
            season=adjudication_data["season"],
            year=adjudication_data["year"],
            type=adjudication_data["type"],
            options=adjudication_data["options"],
            contested_provinces=adjudication_data.get("contested_provinces", []),
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=scheduled_resolution,
        )

        # Create supply centers
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

        # Bulk create all supply centers
        SupplyCenter.objects.bulk_create(supply_centers_to_create)

        # Create units
        units_to_create = []
        for unit in adjudication_data["units"]:
            is_dislodged = unit.get("dislodged", False)

            dislodger_origin = unit.get("dislodged_by", None)
            dislodged_from = None

            if is_dislodged and dislodger_origin:
                dislodged_from = province_lookup.get(dislodger_origin)

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
                        dislodged_from=dislodged_from,
                    )
                )

        # Bulk create all units
        Unit.objects.bulk_create(units_to_create)

        # Create phase states
        nations_with_orders = new_phase.nations_with_possible_orders

        # Prefetch member nations to avoid N+1
        members = list(new_phase.game.members.select_related("nation").all())

        phase_states_to_create = []
        for member in members:
            phase_states_to_create.append(
                new_phase.phase_states.model(
                    member=member,
                    phase=new_phase,
                    has_possible_orders=member.nation.name in nations_with_orders and not member.kicked,
                    orders_confirmed=member.civil_disorder,
                )
            )

        # Bulk create all phase states
        new_phase.phase_states.model.objects.bulk_create(phase_states_to_create)

        self.arm_resolution(new_phase)

        # Mark previous phase as completed
        previous_phase.status = PhaseStatus.COMPLETED
        previous_phase.save()

        self._emit_phase_resolved(previous_phase)

        return new_phase


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
    processing_started_at = models.DateTimeField(null=True, blank=True, editable=False)
    season = models.CharField(max_length=10)
    year = models.IntegerField()
    type = models.CharField(max_length=10)
    scheduled_resolution = models.DateTimeField(null=True, blank=True)
    resolution_job_id = models.BigIntegerField(null=True, blank=True, editable=False)
    options = models.JSONField(default=dict)
    contested_provinces = models.JSONField(default=list)

    class Meta:
        ordering = ["ordinal", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "ordinal"],
                condition=~Q(status=PhaseStatus.COMPLETED),
                name="unique_live_phase_ordinal_per_game",
            )
        ]

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
    def formatted_deadline(self):
        if not self.scheduled_resolution:
            return None
        return format_deadline(self.scheduled_resolution, self.game.fixed_deadline_timezone)

    @property
    def all_orders(self):
        return [order for phase_state in self.phase_states.all() for order in phase_state.orders.all()]

    @cached_property
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
        return [phase_state for phase_state in self.phase_states.all() if phase_state.member.nation.name in nations]

    @property
    def has_unconfirmed_human(self):
        return self.phase_states.filter(
            has_possible_orders=True,
            orders_confirmed=False,
        ).exclude(member__user__profile__kind__in=UserKind.BOT_KINDS).exists()

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
        if self.game.status == GameStatus.COMPLETED:
            raise ValueError("Cannot revert phases in an ended game")

        self.game.phases.filter(ordinal__gt=self.ordinal).delete()

        Order.objects.filter(phase_state__phase=self).delete()

        self.status = PhaseStatus.ACTIVE
        self.scheduled_resolution = self.game.get_scheduled_resolution(self.type)
        self.save()

        self.phase_states.update(orders_confirmed=False)

        Phase.objects.arm_resolution(self)

        emit("phase_started", phase=self)


class PhaseState(BaseModel):
    class OrdersOutcome(models.TextChoices):
        RECEIVED = "received"
        NMR = "nmr"

    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="phase_states")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="phase_states")
    orders_confirmed = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    has_possible_orders = models.BooleanField(default=False)
    deadline_warning_sent_for = models.DateTimeField(null=True, blank=True)
    orders_outcome = models.CharField(
        max_length=8, choices=OrdersOutcome, null=True, blank=True, default=None
    )

    def __str__(self):
        username = self.member.user.username if self.member.user else "Deleted User"
        return f"{username} - {self.phase.name}"

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
