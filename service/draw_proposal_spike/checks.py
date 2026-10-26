from common.checks import Check
from draw_proposal.constants import DrawProposalStatus


class HasNoActiveProposalCheck(Check):
    reason = "already_proposed"

    def check(self, game, actor):
        phase = game.current_phase
        member = game.members.seat_of(actor)
        if phase is None or member is None:
            return True
        return not phase.spike_draw_proposals.active().filter(created_by=member).exists()


class HasNoPendingProposalCheck(Check):
    reason = "proposal_pending"

    def check(self, game, actor):
        phase = game.current_phase
        return phase is None or not phase.spike_draw_proposals.pending().exists()


class IsProposerCheck(Check):
    reason = "not_proposer"

    def check(self, proposal, actor):
        member = proposal.game.members.seat_of(actor)
        return member is not None and proposal.created_by_id == member.pk


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
        member = proposal.game.members.seat_of(actor)
        return member is not None and proposal.votes.filter(member=member).exists()


class HasNotVotedCheck(Check):
    reason = "already_voted"

    def check(self, proposal, actor):
        member = proposal.game.members.seat_of(actor)
        if member is None:
            return True
        return not proposal.votes.filter(member=member, accepted__isnull=False).exists()
