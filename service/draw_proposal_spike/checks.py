from common.checks import Check
from draw_proposal.constants import DrawProposalStatus


class HasNoActiveProposalCheck(Check):
    reason = "already_proposed"

    def check(self, game, actor):
        proposals = game.current_phase.spike_draw_proposals.active()
        return not proposals.filter(created_by__user_id=actor.pk).exists()


class HasNoPendingProposalCheck(Check):
    reason = "proposal_pending"

    def check(self, game, actor):
        return not game.current_phase.spike_draw_proposals.pending().exists()


class IsProposerCheck(Check):
    reason = "not_proposer"

    def check(self, proposal, actor):
        return proposal.created_by.user_id == actor.pk


class IsPendingCheck(Check):
    reason = "not_pending"

    def check(self, proposal, actor):
        return proposal.status == DrawProposalStatus.PENDING


class IsAcceptedCheck(Check):
    def check(self, proposal, actor):
        return proposal.status == DrawProposalStatus.ACCEPTED


class HasVoteCheck(Check):
    reason = "no_vote"

    def check(self, proposal, actor):
        return proposal.votes.filter(member__user_id=actor.pk).exists()


class HasNotVotedCheck(Check):
    reason = "already_voted"

    def check(self, proposal, actor):
        votes = proposal.votes.filter(member__user_id=actor.pk)
        return not votes.filter(accepted__isnull=False).exists()
