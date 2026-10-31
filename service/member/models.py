from datetime import datetime, timezone as dt_timezone
from functools import cached_property

from django.apps import apps
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models, transaction
from django.db.models import Case, Count, F, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.utils import timezone
from common.constants import (
    ActionBlockedReason,
    CommitmentEligibility,
    CommitmentEvent,
    GameStatus,
    MemberActionKey,
    MemberDeparture,
    MemberKind,
    ParticipationStatus,
    PhaseStatus,
    PhaseType,
    UserKind,
)
from common.models import BaseModel
from emit import emit

User = get_user_model()

CIVIL_DISORDER_DETECTED_FROM = datetime(2026, 4, 10, tzinfo=dt_timezone.utc)
REMOVAL_TIMESTAMP_TRUSTED_FROM = datetime(2026, 10, 12, tzinfo=dt_timezone.utc)
CIVIL_DISORDER_NMR_TRIGGER = 2


def commitment_points(kind_lookup):
    return Coalesce(
        Sum(
            Case(
                *[
                    When(**{kind_lookup: kind}, then=Value(points))
                    for kind, points in CommitmentEvent.POINTS.items()
                ],
                output_field=models.IntegerField(),
            )
        ),
        0,
    )


class MemberQuerySet(models.QuerySet):
    def not_replaced(self):
        return self.filter(replaced_by__isnull=True)

    def players(self):
        return self.filter(kind=MemberKind.PLAYER)

    def vacant(self):
        return self.not_replaced().filter(
            models.Q(civil_disorder_at__isnull=False)
            | models.Q(removed_at__isnull=False)
            | models.Q(withdrawn_at__isnull=False)
        )

    def holding_seat(self):
        return self.filter(removed_at__isnull=True, replaced_by__isnull=True)

    def seat_of(self, user):
        if user.pk is None:
            return None
        occupied = self.players().holding_seat().exclude(pk__in=self.vacant())
        return occupied.filter(user_id=user.pk).first()

    def with_commitment_square(self):
        return self.annotate(
            commitment_square=commitment_points("commitment_entries__kind")
        )

    def commitment_squares(self):
        return (
            self.players()
            .filter(game__private=False, game__sandbox=False)
            .with_commitment_square()
            .annotate(
                commitment_submitted=Count(
                    "commitment_entries",
                    filter=Q(commitment_entries__kind=CommitmentEvent.SUBMITTED),
                ),
                commitment_missed=Count(
                    "commitment_entries",
                    filter=Q(commitment_entries__kind=CommitmentEvent.NMR),
                ),
                commitment_events=ArrayAgg(
                    "commitment_entries__kind",
                    filter=Q(commitment_entries__isnull=False)
                    & ~Q(commitment_entries__kind__in=CommitmentEvent.PHASE_KINDS),
                    distinct=True,
                    default=Value([]),
                ),
            )
            .order_by("created_at", "id")
        )

    def with_detail_data(self):
        Phase = apps.get_model("phase", "Phase")
        return self.select_related(
            "nation",
            "user__profile__uploaded_picture",
            "game__victory",
        ).prefetch_related(
            "game__members",
            "game__victory__members",
            models.Prefetch("game__phases", queryset=Phase.objects.defer("options")),
            "nation_preferences__nation",
        )


class MemberManager(models.Manager.from_queryset(MemberQuerySet)):

    def commitment_totals(self, user_ids):
        return dict(
            CommitmentEntry.objects.filter(member__user_id__in=user_ids)
            .order_by()
            .values_list("member__user_id")
            .annotate(total=commitment_points("kind"))
        )

    def hydrate_commitment_totals(self, members):
        members = [
            member for member in members if "commitment_total" not in member.__dict__
        ]
        if not members:
            return
        totals = self.commitment_totals({member.user_id for member in members} - {None})
        for member in members:
            member.commitment_total = totals.get(member.user_id, 0)

    def hand_over_seat(self, member, user):
        ChannelMember = apps.get_model("channel", "ChannelMember")
        PhaseState = apps.get_model("phase", "PhaseState")

        with transaction.atomic():
            replacement = member.game.members.create(user=user)
            ChannelMember.objects.bulk_create(
                [
                    ChannelMember(member=replacement, channel_id=channel_id)
                    for channel_id in member.member_channels.values_list(
                        "channel_id", flat=True
                    )
                ]
            )

            if not member.vacant:
                member.removed_at = timezone.now()
            member.replaced_by = replacement
            member.save(update_fields=["removed_at", "replaced_by"])

            replacement.nation = member.nation
            replacement.save(update_fields=["nation"])

            phase = self._lock_active_phase(member.game)
            if phase is not None:
                self._vacate_phase(member, phase, has_possible_orders=False)
                PhaseState.objects.create(
                    member=replacement,
                    phase=phase,
                    has_possible_orders=member.nation.name
                    in phase.nations_with_possible_orders,
                )
                Phase = apps.get_model("phase", "Phase")
                Phase.objects.arm_resolution(phase)

        return replacement

    def set_nation_preferences(self, member, nations):
        with transaction.atomic():
            member.nation_preferences.all().delete()
            NationPreference.objects.bulk_create(
                [
                    NationPreference(member=member, nation=nation, rank=rank)
                    for rank, nation in enumerate(nations, start=1)
                ]
            )

    def assign_nation(self, member, nation):
        member.nation = nation
        member.save(update_fields=["nation"])

    def clear_nation(self, member):
        member.nation = None
        member.save(update_fields=["nation"])

    def remove(self, member):
        if member.game.status in (GameStatus.PENDING, GameStatus.MUSTERING):
            Channel = apps.get_model("channel", "Channel")
            with transaction.atomic():
                Channel.objects.delete_channels_left_with_one_member(member)
                member.delete()
                member.game.return_to_pending()
            return

        with transaction.atomic():
            member.removed_at = timezone.now()
            member.save(update_fields=["removed_at"])

            phase = self._lock_active_phase(member.game)
            if phase is not None:
                self._vacate_phase(member, phase, orders_confirmed=True)
                Phase = apps.get_model("phase", "Phase")
                Phase.objects.arm_resolution(phase)

    def withdraw(self, member):
        DrawProposal = apps.get_model("draw_proposal", "DrawProposal")
        Phase = apps.get_model("phase", "Phase")
        game = member.game

        with transaction.atomic():
            member.withdrawn_at = timezone.now()
            member.save(update_fields=["withdrawn_at"])
            CommitmentEntry.objects.record(
                member,
                (
                    CommitmentEvent.EARLY_WITHDRAWAL
                    if game.in_first_year
                    else CommitmentEvent.LATE_WITHDRAWAL
                ),
            )

            phase = self._lock_active_phase(game)
            if phase is not None:
                self._vacate_phase(member, phase, orders_confirmed=True)
                Phase.objects.arm_resolution(phase)
                DrawProposal.objects.release_member(phase, member)

            game.refresh_from_db(fields=["status"])
            if game.status == GameStatus.ACTIVE:
                if member.user_id is not None and member.user_id == game.admin_id:
                    game.reassign_admin()
                if game.should_abandon():
                    game.finish(GameStatus.ABANDONED)

            emit(
                "withdrawal",
                game=game,
                actor=member.user,
                nation_name=member.nation.name,
            )

        return member

    def _lock_active_phase(self, game):
        Phase = apps.get_model("phase", "Phase")

        phase = game.current_phase
        if phase is None or Phase.objects.lock_if_active(phase.id) is None:
            return None
        return phase

    def _vacate_phase(self, member, phase, **phase_state_fields):
        Order = apps.get_model("order", "Order")

        phase_states = phase.phase_states.filter(member=member)
        Order.objects.filter(phase_state__in=phase_states).delete()
        phase_states.update(**phase_state_fields)


class Member(BaseModel):
    objects = MemberManager()
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="members"
    )
    game = models.ForeignKey(
        "game.Game", on_delete=models.CASCADE, related_name="members"
    )
    kind = models.CharField(
        max_length=20, choices=MemberKind.KIND_CHOICES, default=MemberKind.PLAYER
    )
    nation = models.ForeignKey(
        "nation.Nation",
        on_delete=models.CASCADE,
        related_name="members",
        null=True,
        blank=True,
    )
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
    replaced_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replaces",
    )

    class Meta:
        indexes = [
            models.Index(fields=["game", "user"]),
            models.Index(fields=["user"]),
            models.Index(fields=["game"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "nation"],
                condition=models.Q(replaced_by__isnull=True),
                name="member_unique_nation_per_game",
            ),
            models.UniqueConstraint(
                fields=["game", "user"],
                condition=models.Q(sandbox=False),
                name="unique_member_per_user_per_game",
            ),
            models.UniqueConstraint(
                fields=["game"],
                condition=models.Q(kind=MemberKind.GAME_MASTER),
                name="member_unique_game_master_per_game",
            ),
        ]

    @cached_property
    def commitment_total(self):
        return CommitmentEntry.objects.filter(member__user_id=self.user_id).aggregate(
            total=commitment_points("kind")
        )["total"]

    @property
    def is_game_master(self):
        return self.kind == MemberKind.GAME_MASTER

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
        return self.replaced_by_id is None and (
            self.civil_disorder or self.removed or self.withdrawn
        )

    @property
    def occupied(self):
        return self.replaced_by_id is None and not self.vacant

    @property
    def replaceable(self):
        return (self.vacant or self.seeking_replacement) and not (
            self.eliminated or self.replaced_by_id is not None
        )

    @property
    def participation_status(self):
        if self.is_game_master:
            return ParticipationStatus.GAME_MASTER
        if self.replaced_by_id is not None:
            return ParticipationStatus.REPLACED
        if self.removed:
            return ParticipationStatus.REMOVED
        if self.withdrawn:
            return ParticipationStatus.WITHDRAWN
        victory = getattr(self.game, "victory", None)
        if victory is not None:
            victor_ids = [member.id for member in victory.members.all()]
            if self.id in victor_ids:
                return (
                    ParticipationStatus.WON
                    if len(victor_ids) == 1
                    else ParticipationStatus.DREW
                )
        if self.eliminated:
            return ParticipationStatus.ELIMINATED
        if self.civil_disorder:
            return ParticipationStatus.CIVIL_DISORDER
        if self.seat_confirmed is True:
            return ParticipationStatus.SEAT_CONFIRMED
        if self.seat_confirmed is False:
            return ParticipationStatus.SEAT_UNCONFIRMED
        if self.game.status == GameStatus.PENDING:
            return ParticipationStatus.JOINED
        return ParticipationStatus.PLAYING

    @property
    def seat_confirmed(self):
        if self.is_game_master or self.game.status != GameStatus.MUSTERING:
            return None
        return self.mustered_at is not None or self.is_bot

    @property
    def is_bot(self):
        return self.user is not None and self.user.profile.is_bot

    @property
    def name(self):
        if self.user is None:
            return "Deleted User"
        return self.user.profile.name

    @property
    def picture(self):
        if self.user is None:
            return None
        return self.user.profile.picture

    def actions_for(self, user):
        game = self.game
        if self.user_id is not None and self.user_id == user.id:
            return game.seat_actions_for(user)
        manages = game.can_manage(user)
        active = game.status == GameStatus.ACTIVE
        actions = []
        if active and self.replaceable:
            user_is_player = any(
                member.user_id == user.id and not member.is_game_master
                for member in game.members.all()
            )
            user_is_game_master = (
                game.game_master_id is not None and game.game_master_id == user.id
            )
            if not user_is_player and not user_is_game_master:
                eligible = (
                    game.commitment_eligibility(user) == CommitmentEligibility.ELIGIBLE
                )
                actions.append(
                    {
                        "key": MemberActionKey.TAKE_OVER,
                        "blocked_reason": (
                            None if eligible else ActionBlockedReason.COMMITMENT_TOO_LOW
                        ),
                    }
                )
            actions.append(
                {"key": MemberActionKey.SHARE_REPLACEMENT_LINK, "blocked_reason": None}
            )
        if (
            manages
            and game.status in (GameStatus.PENDING, GameStatus.MUSTERING)
            and game.can_remove_member(self)
        ):
            actions.append(
                {"key": MemberActionKey.REMOVE_FROM_LOBBY, "blocked_reason": None}
            )
        if (
            manages
            and active
            and not self.is_game_master
            and not self.is_bot
            and not self.left_seat
            and not self.withdrawn
            and not (self.eliminated and self.civil_disorder)
        ):
            actions.append(
                {
                    "key": MemberActionKey.REMOVE_FROM_GAME,
                    "blocked_reason": (
                        None
                        if game.can_remove_member(self)
                        else ActionBlockedReason.NO_MISSED_ORDERS
                    ),
                }
            )
        return actions

    def __str__(self):
        username = self.user.username if self.user else "Deleted User"
        return f"{username} - {self.game.name} - {self.nation.name if self.nation else '-'}"


class NationPreference(BaseModel):
    member = models.ForeignKey(
        "member.Member", on_delete=models.CASCADE, related_name="nation_preferences"
    )
    nation = models.ForeignKey(
        "nation.Nation", on_delete=models.CASCADE, related_name="member_preferences"
    )
    rank = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["rank"]
        unique_together = [["member", "nation"], ["member", "rank"]]

    def __str__(self):
        return f"{self.member} - {self.rank}. {self.nation.name}"


class CommitmentEntryManager(models.Manager):
    def record(self, member, kind):
        game = member.game
        if game.sandbox or game.private:
            return None
        if member.user is None or member.user.profile.kind != UserKind.HUMAN:
            return None
        return self.create(member=member, kind=kind)

    def rebuild(self):
        Phase = apps.get_model("phase", "Phase")
        PhaseState = apps.get_model("phase", "PhaseState")

        with transaction.atomic():
            self.all().delete()

            members = list(
                Member.objects.players()
                .filter(
                    game__sandbox=False,
                    game__private=False,
                    user__profile__kind=UserKind.HUMAN,
                )
                .select_related("game")
            )

            next_phase_created_at = (
                Phase.objects.filter(
                    game_id=OuterRef("phase__game_id"),
                    ordinal__gt=OuterRef("phase__ordinal"),
                )
                .order_by("ordinal")
                .values("created_at")[:1]
            )
            states = (
                PhaseState.objects.filter(
                    member__kind=MemberKind.PLAYER,
                    member__game__sandbox=False,
                    member__game__private=False,
                    member__user__profile__kind=UserKind.HUMAN,
                    has_possible_orders=True,
                    phase__status=PhaseStatus.COMPLETED,
                )
                .annotate(
                    resolved_at=Coalesce(
                        Subquery(next_phase_created_at), F("phase__updated_at")
                    )
                )
                .order_by("member_id", "phase__ordinal")
                .values_list(
                    "member_id", "orders_outcome", "phase__type", "resolved_at"
                )
            )
            states_by_member = {}
            for member_id, *state in states.iterator(chunk_size=10000):
                states_by_member.setdefault(member_id, []).append(tuple(state))

            phases_by_game = {}
            for game_id, year, created_at in (
                Phase.objects.filter(
                    game_id__in={m.game_id for m in members if m.withdrawn_at}
                )
                .order_by("ordinal", "id")
                .values_list("game_id", "year", "created_at")
            ):
                phases_by_game.setdefault(game_id, []).append((year, created_at))

            entries = [
                CommitmentEntry(member=member, kind=kind)
                for member in members
                for kind in self._rebuilt_kinds(
                    member,
                    states_by_member.get(member.id, []),
                    phases_by_game.get(member.game_id, []),
                )
            ]
            self.bulk_create(entries, batch_size=10000)
            return entries

    def _rebuilt_kinds(self, member, states, phases):
        PhaseState = apps.get_model("phase", "PhaseState")

        if (
            member.removed_at is not None
            and member.removed_at >= REMOVAL_TIMESTAMP_TRUSTED_FROM
        ):
            states = [state for state in states if state[2] <= member.removed_at]

        trigger = self._civil_disorder_trigger(states)
        entered_civil_disorder = trigger is not None and (
            member.civil_disorder_at is not None
            or states[trigger][2] < CIVIL_DISORDER_DETECTED_FROM
        )
        if entered_civil_disorder:
            states = states[: trigger + 1]

        kinds = [
            (
                CommitmentEvent.SUBMITTED
                if outcome == PhaseState.OrdersOutcome.RECEIVED
                else CommitmentEvent.NMR
            )
            for outcome, _, _ in states
            if outcome is not None
        ]
        if entered_civil_disorder or member.civil_disorder_at is not None:
            kinds.append(CommitmentEvent.CIVIL_DISORDER)
        if member.withdrawn_at is not None:
            kinds.append(self._withdrawal_kind(member.withdrawn_at, phases))
        if (
            member.game.muster_required
            and member.mustered_at is None
            and member.removed_at is not None
        ):
            kinds.append(CommitmentEvent.MUSTER_NO_SHOW)
        return kinds

    def _civil_disorder_trigger(self, states):
        PhaseState = apps.get_model("phase", "PhaseState")

        last_submitted = max(
            (
                index
                for index, (outcome, _, _) in enumerate(states)
                if outcome == PhaseState.OrdersOutcome.RECEIVED
            ),
            default=-1,
        )
        consecutive_movement_nmrs = 0
        for index, (outcome, phase_type, _) in enumerate(states):
            if phase_type != PhaseType.MOVEMENT:
                continue
            if outcome != PhaseState.OrdersOutcome.NMR:
                consecutive_movement_nmrs = 0
                continue
            consecutive_movement_nmrs += 1
            if (
                consecutive_movement_nmrs >= CIVIL_DISORDER_NMR_TRIGGER
                and index > last_submitted
            ):
                return index
        return None

    def _withdrawal_kind(self, withdrawn_at, phases):
        in_progress = [
            year for year, created_at in phases if created_at <= withdrawn_at
        ]
        if in_progress and in_progress[-1] == phases[0][0]:
            return CommitmentEvent.EARLY_WITHDRAWAL
        return CommitmentEvent.LATE_WITHDRAWAL


class CommitmentEntry(BaseModel):
    objects = CommitmentEntryManager()
    member = models.ForeignKey(
        "member.Member", on_delete=models.CASCADE, related_name="commitment_entries"
    )
    kind = models.CharField(max_length=20, choices=CommitmentEvent.KIND_CHOICES)

    class Meta:
        indexes = [
            models.Index(fields=["member", "kind"], name="commitment_member_kind_idx"),
        ]

    def __str__(self):
        return f"{self.member} - {self.kind}"
