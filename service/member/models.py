from django.apps import apps
from django.db import models, transaction
from django.db.models import Case, Sum, Value, When
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
    UserKind,
)
from common.models import BaseModel
from emit import emit

User = get_user_model()


def commitment_points(kind_lookup):
    return Coalesce(
        Sum(
            Case(
                *[When(**{kind_lookup: kind}, then=Value(points)) for kind, points in CommitmentEvent.POINTS.items()],
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

    def with_commitment_square(self):
        return self.annotate(commitment_square=commitment_points("commitment_entries__kind"))

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

    def hand_over_seat(self, member, user):
        ChannelMember = apps.get_model("channel", "ChannelMember")
        PhaseState = apps.get_model("phase", "PhaseState")

        with transaction.atomic():
            replacement = member.game.members.create(user=user)
            ChannelMember.objects.bulk_create(
                [
                    ChannelMember(member=replacement, channel_id=channel_id)
                    for channel_id in member.member_channels.values_list("channel_id", flat=True)
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
                    has_possible_orders=member.nation.name in phase.nations_with_possible_orders,
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
                CommitmentEvent.EARLY_WITHDRAWAL if game.in_first_year else CommitmentEvent.LATE_WITHDRAWAL,
            )

            phase = self._lock_active_phase(game)
            if phase is not None:
                self._vacate_phase(member, phase, orders_confirmed=True)
                Phase.objects.arm_resolution(phase)
                DrawProposal.objects.apply_withdrawal(member, phase)

            game.refresh_from_db(fields=["status"])
            if game.status == GameStatus.ACTIVE:
                if member.user_id is not None and member.user_id == game.admin_id:
                    game.reassign_admin()
                if game.should_abandon():
                    game.finish(GameStatus.ABANDONED)

            emit("withdrawal", game=game, actor=member.user, nation_name=member.nation.name)

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="members")
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="members")
    kind = models.CharField(max_length=20, choices=MemberKind.KIND_CHOICES, default=MemberKind.PLAYER)
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="members", null=True, blank=True)
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
        return self.replaced_by_id is None and (self.civil_disorder or self.removed or self.withdrawn)

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
                return ParticipationStatus.WON if len(victor_ids) == 1 else ParticipationStatus.DREW
        if self.eliminated:
            return ParticipationStatus.ELIMINATED
        if self.civil_disorder:
            return ParticipationStatus.CIVIL_DISORDER
        if self.game.status == GameStatus.MUSTERING:
            if self.mustered_at is None and not self.is_bot:
                return ParticipationStatus.SEAT_UNCONFIRMED
            return ParticipationStatus.SEAT_CONFIRMED
        if self.game.status == GameStatus.PENDING:
            return ParticipationStatus.JOINED
        return ParticipationStatus.PLAYING

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
                member.user_id == user.id and not member.is_game_master for member in game.members.all()
            )
            user_is_game_master = game.game_master_id is not None and game.game_master_id == user.id
            if not user_is_player and not user_is_game_master:
                eligible = game.commitment_eligibility(user) == CommitmentEligibility.ELIGIBLE
                actions.append({
                    "key": MemberActionKey.TAKE_OVER,
                    "blocked_reason": None if eligible else ActionBlockedReason.COMMITMENT_TOO_LOW,
                })
            actions.append({"key": MemberActionKey.SHARE_REPLACEMENT_LINK, "blocked_reason": None})
        if (
            manages
            and game.status in (GameStatus.PENDING, GameStatus.MUSTERING)
            and game.can_remove_member(self)
        ):
            actions.append({"key": MemberActionKey.REMOVE_FROM_LOBBY, "blocked_reason": None})
        if (
            manages
            and active
            and not self.is_game_master
            and not self.is_bot
            and not self.left_seat
            and not self.withdrawn
            and not (self.eliminated and self.civil_disorder)
        ):
            actions.append({
                "key": MemberActionKey.REMOVE_FROM_GAME,
                "blocked_reason": None if game.can_remove_member(self) else ActionBlockedReason.NO_MISSED_ORDERS,
            })
        return actions

    def __str__(self):
        username = self.user.username if self.user else "Deleted User"
        return f"{username} - {self.game.name} - {self.nation.name if self.nation else '-'}"


class NationPreference(BaseModel):
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="nation_preferences")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="member_preferences")
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


class CommitmentEntry(BaseModel):
    objects = CommitmentEntryManager()
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="commitment_entries")
    kind = models.CharField(max_length=20, choices=CommitmentEvent.KIND_CHOICES)

    def __str__(self):
        return f"{self.member} - {self.kind}"
