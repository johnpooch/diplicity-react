from django.apps import apps
from django.db import models, transaction
from django.contrib.auth import get_user_model
from common.constants import GameStatus
from common.models import BaseModel

User = get_user_model()


class MemberQuerySet(models.QuerySet):
    def not_replaced(self):
        return self.filter(replaced_by__isnull=True)


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

            member.kicked = True
            member.replaced_by = replacement
            member.save(update_fields=["kicked", "replaced_by"])

            replacement.nation = member.nation
            replacement.save(update_fields=["nation"])

            phase = self._lock_active_phase(member.game)
            if phase is not None:
                self._vacate_phase(member, phase)
                PhaseState.objects.create(
                    member=replacement,
                    phase=phase,
                    has_possible_orders=member.nation.name in phase.nations_with_possible_orders,
                )

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
            with transaction.atomic():
                member.delete()
                member.game.return_to_pending()
            return

        with transaction.atomic():
            member.kicked = True
            member.save(update_fields=["kicked"])

            phase = self._lock_active_phase(member.game)
            if phase is not None:
                self._vacate_phase(member, phase)

    def _lock_active_phase(self, game):
        Phase = apps.get_model("phase", "Phase")

        phase = game.current_phase
        if phase is None or Phase.objects.lock_if_active(phase.id) is None:
            return None
        return phase

    def _vacate_phase(self, member, phase):
        Order = apps.get_model("order", "Order")

        phase_states = phase.phase_states.filter(member=member)
        Order.objects.filter(phase_state__in=phase_states).delete()
        phase_states.update(has_possible_orders=False)


class Member(BaseModel):
    objects = MemberManager()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="members")
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="members")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="members", null=True, blank=True)
    won = models.BooleanField(default=False)
    drew = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    kicked = models.BooleanField(default=False)
    nmr_extensions_remaining = models.PositiveSmallIntegerField(default=0)
    civil_disorder = models.BooleanField(default=False)
    seeking_replacement = models.BooleanField(default=False)
    mustered_at = models.DateTimeField(null=True, blank=True)
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
            )
        ]

    @property
    def replaceable(self):
        return (self.kicked or self.civil_disorder or self.seeking_replacement) and not (
            self.eliminated or self.replaced_by_id is not None
        )

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
