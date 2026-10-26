from django.db.models import Manager

from common.commands import command
from draw_proposal.constants import DrawProposalStatus
from emit import emit

from .policies import CanCancelPolicy, CanProposePolicy, CanVotePolicy, ReadyToConcludePolicy
from .querysets import DrawProposalQuerySet


class DrawProposalManager(Manager.from_queryset(DrawProposalQuerySet)):
    @command(requires=CanProposePolicy, locks=["current_phase"])
    def propose(self, game, actor):
        proposal = self.create(
            game=game,
            created_by=game.members.seat_of(actor),
            phase=game.current_phase,
        )
        proposal.create_initial_votes()
        emit("draw_proposal", draw_proposal=proposal)
        self.conclude(proposal)
        return proposal

    @command(requires=CanVotePolicy, locks=["phase"])
    def vote(self, proposal, actor, accepted):
        voter = proposal.game.members.seat_of(actor)
        proposal.votes.get(member=voter).cast(accepted)
        if proposal.status == DrawProposalStatus.REJECTED:
            emit(
                "draw_proposal_rejected",
                game=proposal.game,
                phase=proposal.phase,
                actor=actor,
                nation_name=proposal.created_by.nation.name,
                recipients=[member.user_id for member in proposal.included_members],
            )
        self.conclude(proposal)
        return proposal

    @command(requires=CanCancelPolicy, locks=["phase"])
    def cancel(self, proposal, actor):
        proposal.cancel()
        return proposal

    @command(only_if=ReadyToConcludePolicy, locks=["phase"])
    def conclude(self, proposal):
        victory = proposal.game.finish_with_draw(proposal.phase, proposal.included_members)
        proposal.game.emit_game_ended()
        return victory

    @command()
    def release_member(self, phase, member):
        for proposal in phase.spike_draw_proposals.pending().filter(created_by=member):
            proposal.cancel()
        for proposal in phase.spike_draw_proposals.pending().exclude(created_by=member):
            for vote in proposal.votes.filter(member=member):
                vote.release()
            self.conclude(proposal)
        return phase
