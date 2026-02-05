from datetime import timedelta
import re
import uuid

from django.db import models, transaction
from django.utils import timezone
from django.db.models import Prefetch
from opentelemetry import trace
from common.constants import (
    DeadlineMode,
    GameStatus,
    MovementPhaseDuration,
    NationAssignment,
    PhaseFrequency,
    PhaseStatus,
    PhaseType,
    duration_to_seconds,
)
from common.models import BaseModel
from phase.models import Phase, PhaseState
from phase.utils import calculate_next_fixed_deadline
from member.models import Member
from unit.models import Unit
from supply_center.models import SupplyCenter
from victory.models import Victory
from adjudication import service as adjudication_service

tracer = trace.get_tracer(__name__)


class GameQuerySet(models.QuerySet):

    def with_list_data(self):
        members_prefetch = Prefetch(
            "members",
            queryset=Member.objects.select_related("nation", "user__profile"),
        )

        victory_members_prefetch = Prefetch(
            "victory__members",
            queryset=Member.objects.select_related("user__profile", "nation")
        )

        return self.select_related("variant", "victory").prefetch_related(
            members_prefetch,
            victory_members_prefetch,
            "phases",
        )

    def with_retrieve_data(self):
        members_prefetch = Prefetch(
            "members",
            queryset=Member.objects.select_related("nation", "user__profile"),
        )

        victory_members_prefetch = Prefetch(
            "victory__members",
            queryset=Member.objects.select_related("user__profile", "nation")
        )

        phase_states_prefetch = Prefetch(
            "phase_states",
            queryset=PhaseState.objects.select_related("member__user")
        )

        phases_prefetch = Prefetch(
            "phases",
            queryset=Phase.objects.prefetch_related(phase_states_prefetch)
        )

        return self.select_related("variant", "victory").prefetch_related(
            members_prefetch,
            victory_members_prefetch,
            phases_prefetch,
        )

    def with_related_data(self):

        units_prefetch = Prefetch(
            "units",
            queryset=Unit.objects.select_related(
                "nation",
                "province__parent",
                "dislodged_by",
            ).prefetch_related("province__named_coasts"),
        )

        supply_centers_prefetch = Prefetch(
            "supply_centers",
            queryset=SupplyCenter.objects.select_related(
                "nation",
                "province__parent",
            ).prefetch_related("province__named_coasts"),
        )

        phase_states_prefetch = Prefetch(
            "phase_states",
            queryset=PhaseState.objects.select_related(
                "member__nation",
                "member__user__profile",
            ),
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
            queryset=Member.objects.select_related("nation", "user__profile"),
        )

        victory_members_prefetch = Prefetch(
            "victory__members",
            queryset=Member.objects.select_related("user__profile", "nation")
        )

        return self.select_related("victory").prefetch_related(
            # Variant data with optimized template phase
            "variant__provinces__parent",
            "variant__provinces__named_coasts",
            "variant__nations",
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
                dislodged_by=template_unit.dislodged_by,
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

    def clone_from_phase(self, source_phase, name):
        game = self.create(
            variant=source_phase.game.variant,
            name=name,
            sandbox=True,
            private=True,
            nation_assignment=NationAssignment.ORDERED,
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
            )
            for unit in source_phase.units.all()
        ]
        Unit.objects.bulk_create(units_to_create)

        supply_centers_to_create = [
            SupplyCenter(
                phase=phase,
                nation=sc.nation,
                province=sc.province,
            )
            for sc in source_phase.supply_centers.all()
        ]
        SupplyCenter.objects.bulk_create(supply_centers_to_create)

        game._created_phase = phase
        return game


class Game(BaseModel):

    objects = GameManager()

    id = models.CharField(max_length=150, primary_key=True)
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="games")
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=GameStatus.STATUS_CHOICES, default=GameStatus.PENDING)
    sandbox = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
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
    nation_assignment = models.CharField(
        max_length=20,
        choices=NationAssignment.NATION_ASSIGNMENT_CHOICES,
        default=NationAssignment.RANDOM,
    )
    paused_at = models.DateTimeField(null=True, blank=True)
    nmr_extensions_allowed = models.PositiveSmallIntegerField(default=0)
    deadline_mode = models.CharField(
        max_length=20,
        choices=DeadlineMode.DEADLINE_MODE_CHOICES,
        default=DeadlineMode.DURATION,
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

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self._generate_id()
        super().save(*args, **kwargs)

    def _generate_id(self):
        base_id = re.sub(r"[^a-z0-9]+", "-", self.name.lower())
        base_id = re.sub(r"^-+|-+$", "", base_id)

        if not Game.objects.filter(id=base_id).exists():
            return base_id

        return f"{base_id}-{str(uuid.uuid4())[:8]}"

    @property
    def current_phase(self):
        with tracer.start_as_current_span("game.models.current_phase"):
            # Use prefetched data if available
            if hasattr(self, "active_phases_list"):
                return self.active_phases_list[-1] if self.active_phases_list else None

            phases = list(self.phases.all())
            return phases[-1] if phases else None

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

    def get_phase_duration_seconds(self, phase_type):
        if phase_type == PhaseType.MOVEMENT:
            return self.movement_phase_duration_seconds
        else:
            return self.retreat_phase_duration_seconds

    def get_phase_frequency(self, phase_type):
        if phase_type == PhaseType.MOVEMENT:
            return self.movement_frequency
        else:
            return self.effective_retreat_frequency

    def get_scheduled_resolution(self, phase_type):
        if self.deadline_mode == DeadlineMode.FIXED_TIME:
            frequency = self.get_phase_frequency(phase_type)
            if not frequency or not self.fixed_deadline_time or not self.fixed_deadline_timezone:
                return None
            return calculate_next_fixed_deadline(
                target_time=self.fixed_deadline_time,
                frequency=frequency,
                tz_name=self.fixed_deadline_timezone,
            )
        else:
            phase_duration_seconds = self.get_phase_duration_seconds(phase_type)
            if phase_duration_seconds:
                return timezone.now() + timedelta(seconds=phase_duration_seconds)
            return None

    def can_join(self, user):
        with tracer.start_as_current_span("game.models.can_join"):
            user_is_member = any(member.user.id == user.id for member in self.members.all())
            game_is_pending = self.status == GameStatus.PENDING
            return not user_is_member and game_is_pending

    def can_leave(self, user):
        with tracer.start_as_current_span("game.models.can_leave"):
            user_is_member = any(member.user.id == user.id for member in self.members.all())
            game_is_pending = self.status == GameStatus.PENDING
            return user_is_member and game_is_pending

    def phase_confirmed(self, user):
        with tracer.start_as_current_span("game.models.phase_confirmed"):
            current_phase = self.current_phase
            if current_phase is None:
                return False
            for phase_state in current_phase.phase_states.all():
                if phase_state.member.user.id == user.id and phase_state.orders_confirmed:
                    return True
            return False

    def start(self, current_phase=None, members=None):
        if self.status != GameStatus.PENDING:
            raise ValueError("Game is not pending")

        # Use provided phase/members to avoid unnecessary queries, or fetch if not provided
        if current_phase is None:
            current_phase = self.current_phase
        if members is None:
            members = list(self.members.all())

        adjudication_data = adjudication_service.start(current_phase)

        current_phase.status = PhaseStatus.ACTIVE
        current_phase.options = adjudication_data["options"]
        current_phase.scheduled_resolution = self.get_scheduled_resolution(current_phase.type)
        current_phase.save()

        # Use prefetched nations if available, otherwise fetch
        # variant.nations.all() is already prefetched via with_game_creation_data()
        # Accessing .all() on a prefetched queryset doesn't trigger a new query
        nations = list(self.variant.nations.all())

        if self.nation_assignment == NationAssignment.RANDOM:
            import random

            random.shuffle(members)
        elif self.nation_assignment == NationAssignment.ORDERED:
            members.sort(key=lambda m: m.id)

        now = timezone.now()
        for member, nation in zip(members, nations):
            member.nation = nation
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
        self.save()

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
        ]
