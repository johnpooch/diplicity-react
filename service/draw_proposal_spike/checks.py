from common.checks import Check
from common.constants import PhaseStatus
from draw_proposal.constants import DrawProposalStatus


class IsPhaseActiveCheck(Check):
    reason = "phase_not_active"

    def check(self, phase, actor):
        return phase.status == PhaseStatus.ACTIVE


class HasNoActiveProposalCheck(Check):
    reason = "already_proposed"

    def check(self, phase, actor):
        return not phase.spike_draw_proposals.active().filter(created_by__user_id=actor.pk).exists()


class HasNoPendingProposalCheck(Check):
    reason = "proposal_pending"

    def check(self, phase, actor):
        return not phase.spike_draw_proposals.pending().exists()


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
        return not proposal.votes.filter(member__user_id=actor.pk, accepted__isnull=False).exists()
