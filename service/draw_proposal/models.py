from django.db import models, transaction
from django.utils import timezone
from common.models import BaseModel
from common.constants import GameStatus, PhaseStatus
from draw_proposal.constants import DrawProposalStatus
from emit import emit
from victory.models import Victory


class DrawProposalQuerySet(models.QuerySet):
    def active(self):
        return self.filter(cancelled=False)

    def for_game(self, game):
        return self.filter(game=game)

    def pending_for_phase(self, phase):
        return self.active().filter(phase=phase)

    def with_related_data(self):
        return self.select_related(
            "game",
            "created_by__user__profile",
            "created_by__user__bot_profile",
            "created_by__nation",
            "phase",
        ).prefetch_related(
            "votes__member__user__profile",
            "votes__member__user__bot_profile",
            "votes__member__nation",
        )


class DrawProposalManager(models.Manager):
    def get_queryset(self):
        return DrawProposalQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def for_game(self, game):
        return self.get_queryset().for_game(game)

    def pending_for_phase(self, phase):
        return self.get_queryset().pending_for_phase(phase)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def create_proposal(self, game, created_by):
        phase = game.current_phase

        all_active_members = list(game.members.filter(
            eliminated=False, kicked=False
        ))

        proposal = self.create(
            game=game,
            created_by=created_by,
            phase=phase,
        )

        emit(
            "draw_proposal",
            game=game,
            phase=phase,
            actor=created_by.user,
        )

        votes_to_create = []
        for member in all_active_members:
            if member.civil_disorder:
                votes_to_create.append(
                    DrawVote(
                        proposal=proposal,
                        member=member,
                        included=False,
                        accepted=True,
                    )
                )
            else:
                votes_to_create.append(
                    DrawVote(
                        proposal=proposal,
                        member=member,
                        included=True,
                        accepted=True if member.id == created_by.id else None,
                    )
                )

        DrawVote.objects.bulk_create(votes_to_create)

        # If every active member's vote is already True (e.g. proposer is the
        # only non-CD active member, so all votes are auto-True), the proposal
        # is already ACCEPTED at creation time and needs to be processed.
        if proposal.status == DrawProposalStatus.ACCEPTED:
            proposal.process_acceptance()

        return proposal


class DrawProposal(BaseModel):
    objects = DrawProposalManager()

    game = models.ForeignKey(
        "game.Game", related_name="draw_proposals", on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        "member.Member", related_name="created_draw_proposals", on_delete=models.CASCADE
    )
    phase = models.ForeignKey(
        "phase.Phase", related_name="draw_proposals", on_delete=models.CASCADE
    )
    cancelled = models.BooleanField(default=False)

    @property
    def status(self):
        if self.cancelled:
            return DrawProposalStatus.REJECTED
        if self.phase != self.game.current_phase:
            return DrawProposalStatus.EXPIRED
        votes = list(self.votes.all())
        if any(v.accepted is False for v in votes):
            return DrawProposalStatus.REJECTED
        if all(v.accepted is True for v in votes):
            return DrawProposalStatus.ACCEPTED
        return DrawProposalStatus.PENDING

    @property
    def included_members(self):
        return [vote.member for vote in self.votes.all() if vote.included]

    def process_acceptance(self):
        if self.status != DrawProposalStatus.ACCEPTED:
            return None

        with transaction.atomic():
            victory = Victory.objects.create(
                game=self.game,
                winning_phase=self.phase,
            )

            included_members = self.included_members
            victory.members.set(included_members)

            for member in included_members:
                member.drew = True
                member.save()

            self.game.status = GameStatus.COMPLETED
            self.game.finished_at = timezone.now()
            self.game.save()

            self.phase.status = PhaseStatus.COMPLETED
            self.phase.scheduled_resolution = None
            self.phase.save()

            self.game.emit_game_ended()

            return victory

    class Meta:
        indexes = [
            models.Index(fields=["game"]),
            models.Index(fields=["phase"]),
            models.Index(fields=["created_by"]),
        ]


class DrawVote(BaseModel):
    proposal = models.ForeignKey(
        DrawProposal, related_name="votes", on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        "member.Member", related_name="draw_votes", on_delete=models.CASCADE
    )
    included = models.BooleanField()
    accepted = models.BooleanField(null=True)

    class Meta:
        unique_together = [["proposal", "member"]]
        indexes = [
            models.Index(fields=["proposal"]),
            models.Index(fields=["member"]),
        ]
