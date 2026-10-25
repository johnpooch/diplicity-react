import random
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.constants import (
    CommitmentRequirement,
    DeadlineMode,
    GameStatus,
    MemberDeparture,
    MemberKind,
    MovementPhaseDuration,
    PhaseFrequency,
    PhaseStatus,
    PhaseType,
    PressType,
    UnitType,
    duration_to_seconds,
)
from common.models import BaseModel
from common.slugs import SuffixedSlugIdMixin
from common.timers import TimedModel
from phase.utils import FREQUENCY_INTERVALS, calculate_next_fixed_deadline, deadline_warning_offset, transform_options
from victory.constants import VictoryType

from .lifecycle import GameLifecycle, MemberLifecycle
from .policies import GamePolicy, MemberPolicy
from .query import GameQuerySet, PhaseQuerySet
from .timers import DeadlineWarningTimer, MusterReminderTimer, MusterTimer, ResolutionTimer


class Game(GameLifecycle, GamePolicy, TimedModel, SuffixedSlugIdMixin, BaseModel):
    slug_source = "name"
    timers = (MusterTimer, MusterReminderTimer)
    objects = models.Manager.from_queryset(GameQuerySet)()

    id = models.CharField(max_length=150, primary_key=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    game_master = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="+")
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=GameStatus.STATUS_CHOICES, default=GameStatus.PENDING)
    sandbox = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)
    press_type = models.CharField(max_length=20, choices=PressType.PRESS_TYPE_CHOICES, default=PressType.FULL_PRESS)
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
        max_length=20, choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES, null=True, blank=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    nmr_extensions_allowed = models.PositiveSmallIntegerField(default=0)
    deadline_mode = models.CharField(
        max_length=20, choices=DeadlineMode.DEADLINE_MODE_CHOICES, default=DeadlineMode.FIXED_TIME
    )
    fixed_deadline_time = models.TimeField(null=True, blank=True)
    fixed_deadline_timezone = models.CharField(max_length=50, null=True, blank=True)
    movement_frequency = models.CharField(
        max_length=20, choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES, null=True, blank=True
    )
    retreat_frequency = models.CharField(
        max_length=20, choices=PhaseFrequency.PHASE_FREQUENCY_CHOICES, null=True, blank=True
    )
    muster_required = models.BooleanField(default=False)
    muster_deadline = models.DateTimeField(null=True, blank=True)
    muster_job_id = models.BigIntegerField(null=True, blank=True, editable=False)
    muster_reminder_job_id = models.BigIntegerField(null=True, blank=True, editable=False)

    class Meta:
        managed = False
        db_table = "game_game"

    @property
    def is_paused(self):
        return self.paused_at is not None

    @property
    def is_finished(self):
        return self.status in (GameStatus.COMPLETED, GameStatus.ABANDONED)

    @property
    def players(self):
        return [member for member in self.members.all() if member.is_player and member.replaced_by_id is None]

    @property
    def game_master_member(self):
        return next((member for member in self.members.all() if member.is_game_master), None)

    @property
    def game_master_member_id(self):
        member = self.game_master_member
        return member.id if member is not None else None

    @property
    def unmustered_players(self):
        return [member for member in self.players if member.mustered_at is None and not member.is_bot]

    @property
    def is_mustered(self):
        return not self.unmustered_players

    @property
    def playable_nations(self):
        return [nation for nation in self.variant.nations.all() if not nation.non_playable]

    @property
    def is_full(self):
        return len(self.players) == len(self.playable_nations)

    @property
    def seat_counts(self):
        if self.status == GameStatus.PENDING:
            filled = len(self.players)
        elif self.status == GameStatus.MUSTERING:
            filled = len([member for member in self.players if member.mustered_at is not None or member.is_bot])
        else:
            return None
        return {"filled": filled, "total": len(self.playable_nations)}

    @property
    def seated_user_ids(self):
        user_ids = {member.user_id for member in self.players if member.user_id is not None and member.occupied}
        if self.game_master_id is not None:
            user_ids.add(self.game_master_id)
        return user_ids

    @property
    def phase_ids(self):
        return [phase.id for phase in self.phases.all()]

    @property
    def current_phase(self):
        phases = self.phases.all()
        return phases[len(phases) - 1] if phases else None

    @property
    def current_phase_id(self):
        phase = self.current_phase
        return phase.id if phase is not None else None

    @property
    def latest_completed_phase(self):
        completed = [phase for phase in self.phases.all() if phase.status == PhaseStatus.COMPLETED]
        return completed[-1] if completed else None

    @property
    def nmrd_member_ids(self):
        phase = self.latest_completed_phase
        if phase is None:
            return set()
        return {state.member_id for state in phase.phase_states.all() if state.orders_outcome == PhaseState.NMR}

    @property
    def muster_window_seconds(self):
        return self.effective_phase_duration_seconds(PhaseType.MOVEMENT)

    @property
    def muster_reminder_at(self):
        if self.muster_deadline is None:
            return None
        return self.muster_deadline - deadline_warning_offset(self.muster_window_seconds)

    @property
    def show_short_game_join_warning(self):
        seconds = self.muster_window_seconds
        return seconds is not None and seconds < duration_to_seconds(MovementPhaseDuration.TWENTY_FOUR_HOURS)

    def phase_frequency(self, phase_type):
        if phase_type == PhaseType.MOVEMENT:
            return self.movement_frequency
        return self.retreat_frequency or self.movement_frequency

    def phase_duration_seconds(self, phase_type):
        if phase_type == PhaseType.MOVEMENT:
            return duration_to_seconds(self.movement_phase_duration)
        return duration_to_seconds(self.retreat_phase_duration or self.movement_phase_duration)

    def effective_phase_duration_seconds(self, phase_type):
        if self.deadline_mode == DeadlineMode.FIXED_TIME:
            interval = FREQUENCY_INTERVALS.get(self.phase_frequency(phase_type))
            return int(interval.total_seconds()) if interval else None
        return self.phase_duration_seconds(phase_type)

    def scheduled_resolution(self, phase_type, now, is_first_phase=False):
        if self.deadline_mode == DeadlineMode.FIXED_TIME:
            frequency = self.phase_frequency(phase_type)
            if not frequency or not self.fixed_deadline_time or not self.fixed_deadline_timezone:
                return None
            return calculate_next_fixed_deadline(
                target_time=self.fixed_deadline_time,
                frequency=frequency,
                tz_name=self.fixed_deadline_timezone,
                reference_time=now,
                is_first_phase=is_first_phase,
            )
        seconds = self.phase_duration_seconds(phase_type)
        return now + timedelta(seconds=seconds) if seconds else None

    def nation_assignments(self, members, nations):
        nations_by_id = {nation.id: nation for nation in nations}
        taken = {member.nation_id for member in members if member.nation_id is not None}
        available = {nation.id: nation for nation in nations if nation.id not in taken}
        result = {member.id: nations_by_id[member.nation_id] for member in members if member.nation_id is not None}
        unassigned = [member for member in members if member.nation_id is None]
        rng = random.Random(self.id)
        rng.shuffle(unassigned)
        for member in unassigned:
            choice = next(
                (
                    available.pop(preference.nation_id)
                    for preference in member.nation_preferences.all()
                    if preference.nation_id in available
                ),
                None,
            )
            if choice is None:
                choice = available.pop(rng.choice(sorted(available)))
            result[member.id] = choice
        return result


class Member(MemberLifecycle, MemberPolicy, BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="members")
    kind = models.CharField(max_length=20, choices=MemberKind.KIND_CHOICES, default=MemberKind.PLAYER)
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    sandbox = models.BooleanField(default=False)
    won = models.BooleanField(default=False)
    drew = models.BooleanField(default=False)
    nmr_extensions_remaining = models.PositiveSmallIntegerField(default=0)
    seeking_replacement = models.BooleanField(default=False)
    mustered_at = models.DateTimeField(null=True, blank=True)
    eliminated_at = models.DateTimeField(null=True, blank=True)
    civil_disorder_at = models.DateTimeField(null=True, blank=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    replaced_by = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replaces")

    class Meta:
        managed = False
        db_table = "member_member"
        ordering = ["id"]

    @property
    def is_player(self):
        return self.kind == MemberKind.PLAYER

    @property
    def is_game_master(self):
        return self.kind == MemberKind.GAME_MASTER

    @property
    def is_bot(self):
        return self.user is not None and self.user.profile.is_bot

    @property
    def eliminated(self):
        return self.eliminated_at is not None

    @property
    def civil_disorder(self):
        return self.civil_disorder_at is not None

    @property
    def withdrawn(self):
        return self.withdrawn_at is not None

    @property
    def removed(self):
        return self.removed_at is not None

    @property
    def departure(self):
        if self.eliminated:
            return MemberDeparture.ELIMINATED
        if self.civil_disorder:
            return MemberDeparture.CIVIL_DISORDER
        if self.withdrawn:
            return MemberDeparture.WITHDRAWN
        if self.removed:
            return MemberDeparture.REMOVED
        return None

    @property
    def left_seat(self):
        return self.removed or self.replaced_by_id is not None

    @property
    def vacant(self):
        return self.replaced_by_id is None and (self.civil_disorder or self.removed or self.withdrawn)

    @property
    def occupied(self):
        return self.replaced_by_id is None and not self.vacant

    @property
    def replaceable(self):
        return (self.vacant or self.seeking_replacement) and not (self.eliminated or self.replaced_by_id is not None)

    @property
    def seat_confirmed(self):
        if self.is_game_master or self.game.status != GameStatus.MUSTERING:
            return None
        return self.mustered_at is not None or self.is_bot

    @property
    def removable(self):
        if self.is_game_master or self.left_seat or self.withdrawn:
            return False
        if self.game.status in (GameStatus.PENDING, GameStatus.MUSTERING):
            return True
        if self.game.status != GameStatus.ACTIVE:
            return False
        return self.is_bot or self.civil_disorder or self.id in self.game.nmrd_member_ids

    @property
    def nation_preference_ids(self):
        return [preference.nation.nation_id for preference in self.nation_preferences.all()]


class NationPreference(BaseModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="nation_preferences")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="+")
    rank = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = "member_nationpreference"
        ordering = ["rank"]


class Phase(TimedModel, BaseModel):
    timers = (ResolutionTimer, DeadlineWarningTimer)
    objects = models.Manager.from_queryset(PhaseQuerySet)()

    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True, related_name="phases")
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    ordinal = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=PhaseStatus.STATUS_CHOICES, default=PhaseStatus.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True, editable=False)
    season = models.CharField(max_length=10)
    year = models.IntegerField()
    type = models.CharField(max_length=10)
    scheduled_resolution = models.DateTimeField(null=True, blank=True)
    resolution_job_id = models.BigIntegerField(null=True, blank=True, editable=False)
    warning_job_id = models.BigIntegerField(null=True, blank=True, editable=False)
    options = models.JSONField(default=dict)
    contested_provinces = models.JSONField(default=list)

    class Meta:
        managed = False
        db_table = "phase_phase"
        ordering = ["ordinal", "id"]

    @property
    def name(self):
        return f"{self.season} {self.year}, {self.type}"

    @property
    def remaining_time_seconds(self):
        if self.scheduled_resolution is None or self.status != PhaseStatus.ACTIVE:
            return None
        return max((self.scheduled_resolution - timezone.now()).total_seconds(), 0) or None

    @property
    def nations_with_possible_orders(self):
        return {
            nation
            for nation, options in transform_options(self.options or {}).items()
            if any(province_data for province_data in options.values())
        }

    @property
    def is_resolvable(self):
        states = [state for state in self.phase_states.all() if state.has_possible_orders]
        return bool(self.phase_states.all()) and all(state.orders_confirmed for state in states)

    @property
    def deadline_warning_at(self):
        if self.scheduled_resolution is None:
            return None
        seconds = self.game.effective_phase_duration_seconds(self.type)
        return self.scheduled_resolution - deadline_warning_offset(seconds)


class PhaseState(BaseModel):
    RECEIVED = "received"
    NMR = "nmr"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="phase_states")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="phase_states")
    orders_confirmed = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    has_possible_orders = models.BooleanField(default=False)
    deadline_warning_sent_for = models.DateTimeField(null=True, blank=True)
    orders_outcome = models.CharField(max_length=8, null=True, blank=True, default=None)

    class Meta:
        managed = False
        db_table = "phase_phasestate"
        ordering = ["id"]


class Order(BaseModel):
    phase_state = models.ForeignKey(PhaseState, on_delete=models.CASCADE, related_name="orders")
    order_type = models.CharField(max_length=20, null=True, blank=True)
    is_implicit = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "order_order"


class Unit(BaseModel):
    type = models.CharField(max_length=10, choices=UnitType.UNIT_TYPE_CHOICES)
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="+")
    province = models.ForeignKey("province.Province", on_delete=models.CASCADE, related_name="+")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="units")
    dislodged = models.BooleanField(default=False)
    dislodged_from = models.ForeignKey(
        "province.Province", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )

    class Meta:
        managed = False
        db_table = "unit_unit"
        ordering = ["id"]


class SupplyCenter(models.Model):
    province = models.ForeignKey("province.Province", on_delete=models.CASCADE, related_name="+")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="+")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="supply_centers")

    class Meta:
        managed = False
        db_table = "supply_center_supplycenter"
        ordering = ["id"]


class Victory(BaseModel):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name="victory")
    winning_phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="+")
    members = models.ManyToManyField(Member, related_name="+", db_table="victory_victory_members")

    class Meta:
        managed = False
        db_table = "victory_victory"

    @property
    def type(self):
        count = len(self.members.all())
        if count == 1:
            return VictoryType.SOLO
        if count >= 2:
            return VictoryType.DRAW
        return None

    @property
    def winners(self):
        winner_ids = {member.id for member in self.members.all()}
        return [member for member in self.game.members.all() if member.id in winner_ids]
