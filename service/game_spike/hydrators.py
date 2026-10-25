from django.db.models import Count, Prefetch, prefetch_related_objects

from channel.models import ChannelMessage
from common.hydrators import Hydrator
from draw_proposal.models import DrawVote
from member.models import Member as LegacyMember

from .models import PhaseState, SupplyCenter, Unit


def _prefetch_for(phases, targets, lookup, queryset):
    target_ids = {phase.id for phase in targets}
    prefetch_related_objects([phase for phase in phases if phase.id in target_ids], Prefetch(lookup, queryset=queryset))
    prefetch_related_objects(
        [phase for phase in phases if phase.id not in target_ids], Prefetch(lookup, queryset=queryset.none())
    )


class LatestPhaseStates(Hydrator):
    def hydrate(self, games):
        phases = [phase for game in games for phase in game.phases.all()]
        targets = [game.current_phase for game in games if game.current_phase is not None]
        targets += [game.latest_completed_phase for game in games if game.latest_completed_phase is not None]
        _prefetch_for(
            phases,
            targets,
            "phase_states",
            PhaseState.objects.select_related("member").annotate(order_count=Count("orders")),
        )


class CurrentBoard(Hydrator):
    def hydrate(self, games):
        phases = [phase for game in games for phase in game.phases.all()]
        targets = [game.current_phase for game in games if game.current_phase is not None]
        _prefetch_for(phases, targets, "units", Unit.objects.select_related("nation", "province"))
        _prefetch_for(phases, targets, "supply_centers", SupplyCenter.objects.select_related("nation", "province"))


class UnreadCounts(Hydrator):
    attribute = "total_unread_message_count"
    default = 0

    def values(self, games):
        if not self.user.is_authenticated:
            return {}
        return dict(
            ChannelMessage.objects.unread_by(self.user)
            .filter(channel__game_id__in=[game.pk for game in games])
            .order_by()
            .values_list("channel__game_id")
            .annotate(count=Count("id", distinct=True))
        )


class PendingDrawVotes(Hydrator):
    attribute = "pending_draw_vote"
    default = False

    def values(self, games):
        phase_ids = [game.current_phase_id for game in games if game.current_phase_id is not None]
        if not self.user.is_authenticated or not phase_ids:
            return {}
        game_ids = (
            DrawVote.objects.filter(
                member__user=self.user,
                accepted__isnull=True,
                proposal__cancelled_at__isnull=True,
                proposal__phase_id__in=phase_ids,
            )
            .exclude(proposal__votes__accepted=False)
            .values_list("proposal__game_id", flat=True)
        )
        return {game_id: True for game_id in game_ids}


class CommitmentTotals(Hydrator):
    def hydrate(self, games):
        members = [member for game in games for member in game.members.all()]
        totals = LegacyMember.objects.commitment_totals({member.user_id for member in members} - {None})
        for member in members:
            member.commitment_total = totals.get(member.user_id, 0)
