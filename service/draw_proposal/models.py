from django.db import models, transaction
from common.models import BaseModel
from common.constants import GameStatus
from draw_proposal.constants import DrawProposalStatus


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
            "created_by__nation",
            "phase",
        ).prefetch_related(
            "votes__member__user__profile",
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

    def create_proposal(self, game, created_by, included_member_ids):
        from member.models import Member

        phase = game.current_phase

        all_active_members = list(game.members.filter(
            eliminated=False, kicked=False
        ))

        proposal = self.create(
            game=game,
            created_by=created_by,
            phase=phase,
        )

        from draw_proposal.models import DrawVote

        votes_to_create = []
        for member in all_active_members:
            is_included = member.id in included_member_ids
            is_proposer = member.id == created_by.id
            votes_to_create.append(
                DrawVote(
                    proposal=proposal,
                    member=member,
                    included=is_included,
                    accepted=True if is_proposer else None,
                )
            )

        DrawVote.objects.bulk_create(votes_to_create)

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
    def combined_sc_count(self):
        included_nations = [
            vote.member.nation for vote in self.votes.all() if vote.included
        ]
        return self.phase.supply_centers.filter(
            nation__in=included_nations
        ).count()

    @property
    def included_members(self):
        return [vote.member for vote in self.votes.all() if vote.included]

    def process_acceptance(self):
        from victory.models import Victory

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
            self.game.save()

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
