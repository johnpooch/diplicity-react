from . import models
from .constants import RunStep


class Listener:
    event_type = None

    def create_runs(self, context):
        raise NotImplementedError


class DrawProposalListener(Listener):
    event_type = "draw_proposal"

    def create_runs(self, context):
        proposal = context.draw_proposal
        votes = proposal.votes.filter(
            member__user__bot__isnull=False, accepted__isnull=True
        ).select_related("member__user__bot")
        return models.Run.objects.bulk_create(
            models.Run(
                step=RunStep.DRAW_DECISION,
                bot=vote.member.user.bot,
                member=vote.member,
                phase=proposal.phase,
                draw_proposal=proposal,
            )
            for vote in votes
        )


LISTENERS = {listener.event_type: listener for listener in (DrawProposalListener(),)}
