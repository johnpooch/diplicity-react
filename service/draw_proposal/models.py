from django.db import models
from django.utils import timezone

from common.models import BaseModel

from .constants import DrawProposalStatus
from .managers import DrawProposalManager


class DrawProposal(BaseModel):
    objects = DrawProposalManager()

    game = models.ForeignKey(
        "game.Game",
        related_name="draw_proposals",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        "member.Member",
        related_name="created_draw_proposals",
        on_delete=models.CASCADE,
    )
    phase = models.ForeignKey(
        "phase.Phase",
        related_name="draw_proposals",
        on_delete=models.CASCADE,
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["game"]),
            models.Index(fields=["phase"]),
            models.Index(fields=["created_by"]),
        ]

    @property
    def cancelled(self):
        return self.cancelled_at is not None

    @property
    def status(self):
        if self.cancelled:
            return DrawProposalStatus.CANCELLED
        votes = list(self.votes.all())
        if any(vote.accepted is False for vote in votes):
            return DrawProposalStatus.REJECTED
        if self.phase != self.game.current_phase:
            return DrawProposalStatus.EXPIRED
        if all(vote.accepted is True for vote in votes):
            return DrawProposalStatus.ACCEPTED
        return DrawProposalStatus.PENDING

    @property
    def included_members(self):
        return [vote.member for vote in self.votes.all() if vote.included]

    @property
    def included_member_ids(self):
        return [vote.member_id for vote in self.votes.all() if vote.included]

    @property
    def accepted_count(self):
        return sum(
            1 for vote in self.votes.all() if vote.included and vote.accepted is True
        )

    @property
    def rejected_count(self):
        return sum(1 for vote in self.votes.all() if vote.accepted is False)

    @property
    def pending_count(self):
        return sum(1 for vote in self.votes.all() if vote.accepted is None)

    @property
    def total_votes(self):
        return sum(1 for vote in self.votes.all() if vote.included)

    def create_initial_votes(self):
        members = self.game.members.players().not_replaced()
        votes = [
            DrawVote(
                proposal=self,
                member=member,
                included=not member.vacant,
                accepted=(
                    True if member.vacant or member.id == self.created_by_id else None
                ),
            )
            for member in members.filter(eliminated_at__isnull=True)
        ]
        return DrawVote.objects.bulk_create(votes)

    def cancel(self):
        self.cancelled_at = timezone.now()
        self.save(update_fields=["cancelled_at", "updated_at"])


class DrawVote(BaseModel):
    proposal = models.ForeignKey(
        DrawProposal,
        related_name="votes",
        on_delete=models.CASCADE,
    )
    member = models.ForeignKey(
        "member.Member",
        related_name="draw_votes",
        on_delete=models.CASCADE,
    )
    included = models.BooleanField()
    accepted = models.BooleanField(null=True)

    class Meta:
        unique_together = [["proposal", "member"]]
        indexes = [
            models.Index(fields=["proposal"]),
            models.Index(fields=["member"]),
        ]

    def cast(self, accepted):
        self.accepted = accepted
        self.save(update_fields=["accepted", "updated_at"])

    def release(self):
        self.accepted = True
        self.included = False
        self.save(update_fields=["accepted", "included", "updated_at"])
