from datetime import timedelta
from functools import cached_property
import random
import re
import uuid

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.db.models import (
    Count,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
    prefetch_related_objects,
)
from django.db.models.functions import Coalesce
from opentelemetry import trace
from common.constants import (
    Commitment,
    CommitmentEligibility,
    CommitmentRequirement,
    DeadlineMode,
    GameStatus,
    MinReliability,
    MovementPhaseDuration,
    PhaseFrequency,
    PhaseStatus,
    PhaseType,
    PressType,
    UserKind,
    duration_to_seconds,
)
from common.models import BaseModel
from emit import emit
from phase.models import Phase, PhaseState
from phase.utils import calculate_next_fixed_deadline, FREQUENCY_INTERVALS
from member.models import Member
from unit.models import Unit
from supply_center.models import SupplyCenter
from victory.models import Victory
from channel.models import ChannelMember, ChannelMessage
from adjudicator import service as adjudication_service
from game.utils import assign_nations

tracer = trace.get_tracer(__name__)


class GameQuerySet(models.QuerySet):

    def with_total_unread_counts(self, user):
        if not user.is_authenticated:
            return self.annotate(
                total_unread_message_count=Value(0, output_field=IntegerField())
            )
        last_read_subquery = Subquery(
            ChannelMember.objects.filter(
                channel=OuterRef("channel"),
                member__user=user,
            ).values("last_read_at")[:1]
        )
        unread_count_subquery = (
            ChannelMessage.objects.filter(
                channel__game=OuterRef("pk"),
                channel__member_channels__member__user=user,
                created_at__gt=last_read_subquery,
            )
            .exclude(sender__user=user)
            .order_by()
            .values("channel__game")
            .annotate(count=Count("id", distinct=True))
            .values("count")
        )
        return self.annotate(
            total_unread_message_count=Coalesce(
                Subquery(unread_count_subquery, output_field=IntegerField()),
                Value(0),
            )
        )

    def with_list_data(self):
        members_prefetch = Prefetch(
            "members",
            queryset=Member.objects.not_replaced()
            .select_related("nation", "user__profile__uploaded_picture")
            .prefetch_related("nation_preferences__nation"),
        )

        victory_members_prefetch = Prefetch(
            "victory__members",
            queryset=Member.objects.select_related("user__profile__uploaded_picture", "nation"),
        )

        current_phase_ids = (
            Phase.objects.order_by("game_id", "-ordinal", "-id")
            .distinct("game_id")
            .values("id")
        )
        latest_completed_phase_ids = (
            Phase.objects.filter(status=PhaseStatus.COMPLETED)
            .order_by("game_id", "-ordinal", "-id")
            .distinct("game_id")
            .values("id")
        )
        phase_states_prefetch = Prefetch(
            "phase_states",
            queryset=PhaseState.objects.filter(
                Q(phase__in=current_phase_ids) | Q(phase__in=latest_completed_phase_ids)
            )
            .select_related("member")
            .annotate(order_count=Count("orders")),
        )
        current_units_prefetch = Prefetch(
            "units",
            queryset=Unit.objects.filter(phase__in=current_phase_ids)
            .select_related("nation", "province"),
        )
        current_supply_centers_prefetch = Prefetch(
            "supply_centers",
            queryset=SupplyCenter.objects.filter(phase__in=current_phase_ids)
            .select_related("nation", "province"),
        )
        phases_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.only(
                "id",
                "ordinal",
                "season",
                "year",
                "type",
                "status",
                "scheduled_resolution",
                "game_id",
                "variant_id",
            ).prefetch_related(
                phase_states_prefetch,
                current_units_prefetch,
                current_supply_centers_prefetch,
            ),
        )

        return self.select_related("variant", "victory", "game_master__profile__uploaded_picture").prefetch_related(
            members_prefetch,
            victory_members_prefetch,
            phases_prefetch,
        )

    def with_retrieve_data(self):
        members_prefetch = Prefetch(
            "members",
            queryset=Member.objects.not_replaced()
            .select_related("nation__flag", "user__profile__uploaded_picture")
            .prefetch_related("nation_preferences__nation"),
        )

        victory_members_prefetch = Prefetch(
            "victory__members",
            queryset=Member.objects.select_related("user__profile__uploaded_picture", "nation__flag")
        )

        current_phase_ids = (
            Phase.objects.order_by("game_id", "-ordinal", "-id")
            .distinct("game_id")
            .values("id")
        )
        latest_completed_phase_ids = (
            Phase.objects.filter(status=PhaseStatus.COMPLETED)
            .order_by("game_id", "-ordinal", "-id")
            .distinct("game_id")
            .values("id")
        )
        phase_states_prefetch = Prefetch(
            "phase_states",
            queryset=PhaseState.objects.filter(
                Q(phase__in=current_phase_ids) | Q(phase__in=latest_completed_phase_ids)
            ).select_related("member__user").annotate(
                order_count=Count("orders")
            )
        )

        phases_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.defer("options").prefetch_related(phase_states_prefetch)
        )

        return self.select_related("variant", "victory", "game_master__profile__uploaded_picture").prefetch_related(
            members_prefetch,
            victory_members_prefetch,
            phases_prefetch,
        )

    def with_related_data(self):

        units_prefetch = Prefetch(
            "units",
            queryset=Unit.objects.select_related(
                "nation__flag",
                "province__parent",
                "dislodged_from",
            ).prefetch_related("province__named_coasts"),
        )

        supply_centers_prefetch = Prefetch(
            "supply_centers",
            queryset=SupplyCenter.objects.select_related(
                "nation__flag",
                "province__parent",
            ).prefetch_related("province__named_coasts"),
        )

        phase_states_prefetch = Prefetch(
            "phase_states",
            queryset=PhaseState.objects.select_related(
                "member__nation__flag",
                "member__user__profile__uploaded_picture",
            ).annotate(order_count=Count("orders")),
        )

        template_phase_prefetch = Prefetch(
            "variant__phases",
            queryset=Phase.objects.filter(game=None, status=PhaseStatus.TEMPLATE).prefetch_related(
                units_prefetch,
                supply_centers_prefetch,
                phase_states_prefetch,
            ),
            to_attr="template_phases",
        )

        game_phases_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.prefetch_related(
                units_prefetch,
                supply_centers_prefetch,
                phase_states_prefetch,
            ),
        )

        members_prefetch = Prefetch(
            "members",
            queryset=Member.objects.not_replaced()
            .select_related("nation__flag", "user__profile__uploaded_picture")
            .prefetch_related("nation_preferences__nation"),
        )

        victory_members_prefetch = Prefetch(
            "victory__members",
            queryset=Member.objects.select_related("user__profile__uploaded_picture", "nation__flag")
        )

        return self.select_related("victory", "game_master__profile__uploaded_picture").prefetch_related(
            # Variant data with optimized template phase
            "variant__provinces__parent",
            "variant__provinces__named_coasts",
            "variant__nations__flag",
            template_phase_prefetch,
            # Game phases data
            game_phases_prefetch,
            # Members data
            members_prefetch,
            # Victory data
            victory_members_prefetch,
        )


class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    def with_total_unread_counts(self, user):
        return self.get_queryset().with_total_unread_counts(user)

    def with_list_data(self):
        return self.get_queryset().with_list_data()

    def with_retrieve_data(self):
        return self.get_queryset().with_retrieve_data()

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def create_from_template(self, variant, **kwargs):
        template_phase = variant.template_phase
        game = self.create(variant=variant, **kwargs)

        phase = game.phases.create(
            game=game,
            variant=variant,
            season=template_phase.season,
            year=template_phase.year,
            type=template_phase.type,
            status=PhaseStatus.PENDING,
            ordinal=1,
        )

        from unit.models import Unit

        units_to_create = [
            Unit(
                phase=phase,
                type=template_unit.type,
                nation=template_unit.nation,
                province=template_unit.province,
                dislodged=template_unit.dislodged,
                dislodged_from=template_unit.dislodged_from,
            )
            for template_unit in template_phase.units.all()
        ]
        Unit.objects.bulk_create(units_to_create)

        from supply_center.models import SupplyCenter

        supply_centers_to_create = [
            SupplyCenter(
                phase=phase,
                nation=template_sc.nation,
                province=template_sc.province,
            )
            for template_sc in template_phase.supply_centers.all()
        ]
        SupplyCenter.objects.bulk_create(supply_centers_to_create)

        # Store phase on game object to avoid querying for it later
        game._created_phase = phase
        return game

    def create_sandbox(self, user, *, name, variant, **kwargs):
        kwargs.setdefault("sandbox", True)
        kwargs.setdefault("private", True)
        kwargs.setdefault("movement_phase_duration", None)

        with transaction.atomic():
            game = self.create_from_template(variant, name=name, **kwargs)

            nations_list = [n for n in variant.nations.all() if not n.non_playable]
            members_to_create = [Member(game=game, user=user, sandbox=True) for _ in nations_list]
            created_members = Member.objects.bulk_create(members_to_create)

            current_phase = getattr(game, "_created_phase", None)
            if current_phase is None:
                current_phase = game.phases.first()

            game.start(current_phase=current_phase, members=created_members)

            if hasattr(game, "_created_phase"):
                delattr(game, "_created_phase")

        return game

    def clone_from_phase(self, source_phase, name):
        game = self.create(
            variant=source_phase.game.variant,
            name=name,
            sandbox=True,
            private=True,
            movement_phase_duration=None,
        )

        phase = game.phases.create(
            game=game,
            variant=source_phase.game.variant,
            season=source_phase.season,
            year=source_phase.year,
            type=source_phase.type,
            status=PhaseStatus.PENDING,
            ordinal=1,
        )

        units_to_create = [
            Unit(
                phase=phase,
                type=unit.type,
                nation=unit.nation,
                province=unit.province,
                dislodged=unit.dislodged,
                dislodged_from=unit.dislodged_from,
            )
            for unit in source_phase.units.select_related("nation", "province", "dislodged_from")
        ]
        Unit.objects.bulk_create(units_to_create)

        supply_centers_to_create = [
            SupplyCenter(
                phase=phase,
                nation=sc.nation,
                province=sc.province,
            )
            for sc in source_phase.supply_centers.select_related("nation", "province")
        ]
        SupplyCenter.objects.bulk_create(supply_centers_to_create)

        game._created_phase = phase
        return game


class Game(BaseModel):

    objects = GameManager()

    id = models.CharField(max_length=150, primary_key=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_games",
    )
    game_master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="game_master_games",
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administered_games",
    )
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="games")
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=GameStatus.STATUS_CHOICES, default=GameStatus.PENDING)
    sandbox = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)
    press_type = models.CharField(
        max_length=20,
        choices=PressType.PRESS_TYPE_CHOICES,
        default=PressType.FULL_PRESS,
    )
    min_reliability = models.CharField(
        max_length=20,
        choices=MinReliability.MIN_RELIABILITY_CHOICES,
        default=MinReliability.OPEN,
    )
    commitment_requirement = models.CharField(
        max_length=20,
        choices=CommitmentRequirement.COMMITMENT_REQUIREMENT_CHOICES,
        default=CommitmentRequirement.OPEN,
    )
    movement_phase_duration = models.CharField(
        max_length=20,
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        null=True,
        blank=True,
        default=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )
    retreat_phase_duration = models.CharField(
        max_length=20,
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    nmr_extensions_allowed = models.PositiveSmallIntegerField(default=0)
    deadline_mode = models.CharField(
        max_length=20,
        choices=DeadlineMode.DEADLINE_MODE_CHOICES,
        default=DeadlineMode.FIXED_TIME,
    )
    fixed_deadline_time = models.TimeField(null=True, blank=True)
    fixed_deadline_timezone = models.CharField(max_length=50, null=True, blank=True)
    movement_frequency = models.CharField(
        max_length=20,
        choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES,
        null=True,
        blank=True,
    )
    retreat_frequency = models.CharField(
        max_length=20,
        choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES,
        null=True,
        blank=True,
    )
    muster_required = models.BooleanField(default=False)
    muster_deadline = models.DateTimeField(null=True, blank=True)
    muster_job_id = models.BigIntegerField(null=True, blank=True, editable=False)
    muster_reminder_job_id = models.BigIntegerField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self.id:
            super().save(*args, **kwargs)
            return

        base_id = self._generate_base_id()
        self.id = self._generate_id(base_id)
        kwargs.setdefault("force_insert", True)

        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError:
            self.id = self._suffixed_id(base_id)
            super().save(*args, **kwargs)

    def _generate_base_id(self):
        base_id = re.sub(r"[^a-z0-9]+", "-", self.name.lower())
        return re.sub(r"^-+|-+$", "", base_id)

    def _generate_id(self, base_id):
        if Game.objects.filter(id=base_id).exists():
            return self._suffixed_id(base_id)

        return base_id

    def _suffixed_id(self, base_id):
        return f"{base_id}-{str(uuid.uuid4())[:8]}"

    @property
    def current_phase(self):
        with tracer.start_as_current_span("game.models.current_phase"):
            # Use prefetched data if available
            if hasattr(self, "active_phases_list"):
                return self.active_phases_list[-1] if self.active_phases_list else None

            if "phases" in getattr(self, "_prefetched_objects_cache", {}):
                phases = list(self.phases.all())
                return phases[-1] if phases else None

            return self.phases.order_by("ordinal", "id").last()

    @property
    def movement_phase_duration_seconds(self):
        return duration_to_seconds(self.movement_phase_duration)

    @property
    def retreat_phase_duration_seconds(self):
        duration = self.retreat_phase_duration or self.movement_phase_duration
        return duration_to_seconds(duration)

    @property
    def effective_retreat_frequency(self):
        return self.retreat_frequency or self.movement_frequency

    @property
    def is_paused(self):
        return self.paused_at is not None

    @property
    def manager_label(self):
        return "the Game Master" if self.game_master_id is not None else "the game creator"

    @property
    def anonymity_active(self):
        return self.anonymous and self.status != GameStatus.COMPLETED

    @property
    def bot_members(self):
        return self.members.filter(user__profile__kind__in=UserKind.BOT_KINDS).select_related("user")

    @cached_property
    def nmrd_member_ids(self):
        with tracer.start_as_current_span("game.models.nmrd_member_ids"):
            completed = [p for p in self.phases.all() if p.status == PhaseStatus.COMPLETED]
            if not completed:
                return set()
            latest = max(completed, key=lambda p: p.ordinal)
            return {
                phase_state.member_id
                for phase_state in latest.phase_states.all()
                if phase_state.orders_outcome == PhaseState.OrdersOutcome.NMR
            }

    def get_phase_duration_seconds(self, phase_type):
        if phase_type == PhaseType.MOVEMENT:
            return self.movement_phase_duration_seconds
        else:
            return self.retreat_phase_duration_seconds

    def get_effective_phase_duration_seconds(self, phase_type):
        if self.deadline_mode == DeadlineMode.FIXED_TIME:
            frequency = self.get_phase_frequency(phase_type)
            interval = FREQUENCY_INTERVALS.get(frequency) if frequency else None
            return int(interval.total_seconds()) if interval else None
        return self.get_phase_duration_seconds(phase_type)

    def get_phase_frequency(self, phase_type):
        if phase_type == PhaseType.MOVEMENT:
            return self.movement_frequency
        else:
            return self.effective_retreat_frequency

    def get_scheduled_resolution(self, phase_type, is_first_phase=False, reference_time=None):
        if self.deadline_mode == DeadlineMode.FIXED_TIME:
            frequency = self.get_phase_frequency(phase_type)
            if not frequency or not self.fixed_deadline_time or not self.fixed_deadline_timezone:
                return None
            return calculate_next_fixed_deadline(
                target_time=self.fixed_deadline_time,
                frequency=frequency,
                tz_name=self.fixed_deadline_timezone,
                reference_time=reference_time,
                is_first_phase=is_first_phase,
            )
        else:
            phase_duration_seconds = self.get_phase_duration_seconds(phase_type)
            if phase_duration_seconds:
                return timezone.now() + timedelta(seconds=phase_duration_seconds)
            return None

    def can_join(self, user):
        with tracer.start_as_current_span("game.models.can_join"):
            if self.game_master_id is not None and self.game_master_id == user.id:
                return False
            user_is_member = any(
                member.user_id is not None and member.user_id == user.id
                for member in self.members.all()
            )
            game_is_pending = self.status == GameStatus.PENDING
            return not user_is_member and game_is_pending

    def commitment_eligibility(self, user):
        if not user.is_authenticated:
            return None
        commitment = user.profile.commitment
        if commitment == Commitment.LOW and not self.private:
            return CommitmentEligibility.LOW_LOCKED
        if (
            self.commitment_requirement == CommitmentRequirement.COMMITTED
            and commitment != Commitment.HIGH
        ):
            return CommitmentEligibility.COMMITTED_LOCKED
        return CommitmentEligibility.ELIGIBLE

    def can_leave(self, user):
        with tracer.start_as_current_span("game.models.can_leave"):
            user_is_member = any(
                member.user_id is not None and member.user_id == user.id
                for member in self.members.all()
            )
            game_is_unstarted = self.status in (GameStatus.PENDING, GameStatus.MUSTERING)
            return user_is_member and game_is_unstarted

    def can_delete(self, user):
        with tracer.start_as_current_span("game.models.can_delete"):
            if (
                self.status in (GameStatus.PENDING, GameStatus.MUSTERING)
                and self.game_master_id is not None
                and self.game_master_id == user.id
            ):
                return True
            if not self.sandbox:
                return False
            return any(
                member.user_id is not None and member.user_id == user.id
                for member in self.members.all()
            )

    def can_manage(self, user):
        with tracer.start_as_current_span("game.models.can_manage"):
            return self.admin_id == user.id

    def can_remove_member(self, member):
        with tracer.start_as_current_span("game.models.can_remove_member"):
            if member.kicked or member.replaced_by_id is not None:
                return False
            if self.status in (GameStatus.PENDING, GameStatus.MUSTERING):
                return True
            if self.status != GameStatus.ACTIVE:
                return False
            if member.is_bot:
                return True
            return member.civil_disorder or member.id in self.nmrd_member_ids

    def get_public_press(self):
        return self.channels.get(private=False)

    def seat(self, user):
        member = self.members.create(user=user)
        self.get_public_press().member_channels.create(member=member)
        return member

    def reassign_admin(self):
        with tracer.start_as_current_span("game.models.reassign_admin"):
            candidates = list(
                self.members.filter(kicked=False, civil_disorder=False, user__isnull=False)
                .exclude(user_id=self.admin_id)
            )
            if not candidates:
                return

            new_admin = random.choice(candidates).user
            self.admin = new_admin
            self.save(update_fields=["admin"])

            emit("game_admin_reassigned", game=self)

    def notification_user_ids(self, exclude_user_id=None, active_only=False):
        members = self.members.filter(eliminated=False, kicked=False) if active_only else self.members.all()
        user_ids = {
            member.user_id for member in members
            if member.user_id is not None
        }
        if self.game_master_id is not None:
            user_ids.add(self.game_master_id)
        if exclude_user_id is not None:
            user_ids.discard(exclude_user_id)
        return list(user_ids)

    def _with_game_master(self, user_ids):
        result = set(user_ids)
        if self.game_master_id is not None:
            result.add(self.game_master_id)
        return result

    def member_user_ids(self, include_gm=False):
        ids = {m.user_id for m in self.members.all() if m.user_id is not None}
        return self._with_game_master(ids) if include_gm else ids

    def active_member_user_ids(self, include_gm=False):
        active = self.members.filter(eliminated=False, kicked=False, civil_disorder=False)
        ids = {m.user_id for m in active if m.user_id is not None}
        return self._with_game_master(ids) if include_gm else ids

    def winner_members(self):
        victory = Victory.objects.filter(game=self).prefetch_related("members").first()
        return list(victory.members.all()) if victory is not None else []

    def winner_user_ids(self):
        return {m.user_id for m in self.winner_members() if m.user_id is not None}

    def phase_confirmed(self, user):
        with tracer.start_as_current_span("game.models.phase_confirmed"):
            current_phase = self.current_phase
            if current_phase is None:
                return False
            for phase_state in current_phase.phase_states.all():
                if phase_state.member.user_id is not None and phase_state.member.user_id == user.id and phase_state.orders_confirmed:
                    return True
            return False

    def start(self, current_phase=None, members=None):
        if self.status not in (GameStatus.PENDING, GameStatus.MUSTERING):
            raise ValueError("Game is not pending")

        with transaction.atomic():
            # Use provided phase/members to avoid unnecessary queries, or fetch if not provided
            if current_phase is None:
                current_phase = self.current_phase
            if members is None:
                members = list(self.members.all())
            prefetch_related_objects(members, "nation_preferences")

            adjudication_data = adjudication_service.start(current_phase)

            current_phase.status = PhaseStatus.ACTIVE
            current_phase.options = adjudication_data["options"]
            current_phase.scheduled_resolution = self.get_scheduled_resolution(current_phase.type, is_first_phase=True)
            current_phase.save()

            # Use prefetched nations if available, otherwise fetch
            # variant.nations.all() is already prefetched via with_game_creation_data()
            # Accessing .all() on a prefetched queryset doesn't trigger a new query
            nations = [n for n in self.variant.nations.all() if not n.non_playable]

            assignments = assign_nations(self.id, members, nations)

            now = timezone.now()
            for member in members:
                member.nation = assignments[member.id]
                member.nmr_extensions_remaining = self.nmr_extensions_allowed
                member.updated_at = now

            # Use bulk_update to avoid n+1 queries
            Member.objects.bulk_update(members, ["nation", "nmr_extensions_remaining", "updated_at"])

            nations_with_orders = current_phase.nations_with_possible_orders
            phase_states_to_create = [
                PhaseState(
                    phase=current_phase,
                    member=member,
                    has_possible_orders=member.nation.name in nations_with_orders,
                )
                for member in members
            ]
            PhaseState.objects.bulk_create(phase_states_to_create)

            self.status = GameStatus.ACTIVE
            self.started_at = timezone.now()
            self.save()

            emit("game_start", game=self)
            emit("phase_started", phase=current_phase)

    def finish(self, status):
        with transaction.atomic():
            self.status = status
            self.finished_at = timezone.now()
            self.save()

            for phase in self.phases.exclude(status=PhaseStatus.COMPLETED):
                phase.status = PhaseStatus.COMPLETED
                phase.scheduled_resolution = None
                phase.save()

    def emit_game_ended(self):
        try:
            victory = Victory.objects.prefetch_related("members").get(game=self)
        except Victory.DoesNotExist:
            return

        if victory.members.count() >= 2:
            emit("game_draw", game=self)
        else:
            emit("game_solo_win", game=self)
            emit("game_solo_loss", game=self)

    def start_if_full(self):
        if self.status != GameStatus.PENDING:
            return False
        playable_nations = self.variant.nations.filter(non_playable=False).count()
        if self.members.count() != playable_nations:
            return False
        self.start()
        return True

    def pause(self):
        if self.status != GameStatus.ACTIVE:
            raise ValueError("Can only pause an active game")
        if self.is_paused:
            raise ValueError("Game is already paused")
        self.paused_at = timezone.now()
        self.save()

    @transaction.atomic
    def unpause(self):
        if self.status != GameStatus.ACTIVE:
            raise ValueError("Can only unpause an active game")
        if not self.is_paused:
            raise ValueError("Game is not paused")

        pause_duration = timezone.now() - self.paused_at
        current_phase = self.current_phase

        if current_phase and current_phase.scheduled_resolution:
            current_phase.scheduled_resolution += pause_duration
            current_phase.save()

        self.paused_at = None
        self.save()

    def delete_if_empty_pending(self):
        human_members = self.members.exclude(user__profile__kind__in=UserKind.BOT_KINDS)
        if self.status in (GameStatus.PENDING, GameStatus.MUSTERING) and not human_members.exists():
            self.delete()
            return True
        return False

    def extend_deadline(self, duration):
        if self.status != GameStatus.ACTIVE:
            raise ValueError("Can only extend deadline for an active game")
        if self.is_paused:
            raise ValueError("Cannot extend deadline while game is paused")

        current_phase = self.current_phase
        if not current_phase or not current_phase.scheduled_resolution:
            raise ValueError("No active phase with a scheduled resolution")

        extension_seconds = duration_to_seconds(duration)
        if not extension_seconds:
            raise ValueError("Invalid duration")

        current_phase.scheduled_resolution += timedelta(seconds=extension_seconds)
        current_phase.save()

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["variant"]),
            models.Index(fields=["muster_deadline"]),
        ]
