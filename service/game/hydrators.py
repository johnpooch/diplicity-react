from channel.policies import can_create_channel
from common.constants import DeadlineMode
from common.loaders import Hydrator
from member.loaders import MemberLoader

from .models import Game


class ListPhasesHydrator(Hydrator):
    def hydrate(self, games, actor):
        Game.objects.hydrate_list_phases(games)


class RetrievePhasesHydrator(Hydrator):
    def hydrate(self, games, actor):
        Game.objects.hydrate_retrieve_phases(games)


class TotalUnreadCountsHydrator(Hydrator):
    def hydrate(self, games, actor):
        Game.objects.hydrate_total_unread_counts(games, actor)


class GameMembersHydrator(Hydrator):
    def hydrate(self, games, actor):
        members = [member for game in games for member in game.members.all()]
        members += [
            member
            for game in games
            if hasattr(game, "victory")
            for member in game.victory.members.all()
        ]
        MemberLoader.hydrate(members, actor)


class ViewerPermissionsHydrator(Hydrator):
    def hydrate(self, games, actor):
        signed_in = actor.is_authenticated
        for game in games:
            game.viewer_can_join = signed_in and game.can_join(actor)
            game.viewer_can_leave = signed_in and game.can_leave(actor)
            game.viewer_can_withdraw = signed_in and game.can_withdraw(actor)
            game.viewer_can_delete = signed_in and game.can_delete(actor)
            game.viewer_can_manage = signed_in and game.can_manage(actor)
            game.viewer_join_blocked_reason = (
                game.join_decision(actor).reason if signed_in else None
            )
            game.viewer_muster_status = game.muster_status(actor)


class ViewerOrdersHydrator(Hydrator):
    def hydrate(self, games, actor):
        for game in games:
            game.viewer_phase_confirmed = (
                actor.is_authenticated and game.phase_confirmed(actor)
            )
            game.viewer_order_status = self.order_status(game, actor)
            game.viewer_member_status = self.member_status(game, actor)

    def order_status(self, game, actor):
        if game.sandbox:
            return None
        if not actor.is_authenticated or game.status != "active":
            return None
        current_phase = game.current_phase
        if current_phase is None:
            return None
        for phase_state in current_phase.phase_states.all():
            if phase_state.member.user_id == actor.id:
                if not phase_state.member.occupied:
                    return None
                if phase_state.orders_confirmed:
                    return "orders_submitted"
                if not phase_state.has_possible_orders:
                    return "no_orders_required"
                if phase_state.order_count == 0:
                    return "orders_required"
                if game.deadline_mode == DeadlineMode.FIXED_TIME:
                    return "orders_submitted"
                return "orders_not_confirmed"
        return None

    def member_status(self, game, actor):
        if game.sandbox:
            return None
        if not actor.is_authenticated:
            return []
        current_member = next(
            (m for m in game.members.all() if m.user_id == actor.id), None
        )
        if current_member is None:
            return []
        statuses = []
        if current_member.civil_disorder:
            statuses.append("civil_disorder")
        phases = list(game.phases.all())
        completed_phases = [p for p in phases if p.status == "completed"]
        if completed_phases:
            prev_phase = max(completed_phases, key=lambda p: p.ordinal)
            for phase_state in prev_phase.phase_states.all():
                if phase_state.member.user_id == actor.id:
                    if phase_state.orders_outcome == "nmr":
                        statuses.append("nmr")
                    break
        return statuses


class ViewerActionsHydrator(Hydrator):
    def hydrate(self, games, actor):
        for game in games:
            game.viewer_actions = game.actions_for(actor)
            game.viewer_player_list_actions = game.player_list_actions_for(actor)
            game.viewer_can_create_channel = (
                actor.is_authenticated
                and can_create_channel(game, self.seated_member(game, actor))
            )

    def seated_member(self, game, actor):
        return next(
            (
                member
                for member in game.members.all()
                if member.user_id == actor.id and not member.left_seat
            ),
            None,
        )
