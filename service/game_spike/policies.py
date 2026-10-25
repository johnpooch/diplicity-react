from channel.policies import can_create_channel
from common.constants import (
    CommitmentBand,
    Commitment,
    CommitmentEligibility,
    CommitmentRequirement,
    DeadlineMode,
    DeniedReason,
    GameActionKey,
    GameStatus,
    MemberStatus,
    MusterStatus,
    MyGameResult,
    MyGamesSection,
    MyGameStateKind,
    OrderStatus,
)
from common.policies import ALLOW, deny

UNSTARTED = (GameStatus.PENDING, GameStatus.MUSTERING)


class GamePolicy:
    action_decisions = {
        GameActionKey.JOIN: "can_join",
        GameActionKey.CONFIRM_SEAT: "can_confirm_seat",
        GameActionKey.EDIT_NATION_PREFERENCES: "can_edit_nation_preferences",
        GameActionKey.ASSIGN_NATIONS: "can_assign_nations",
        GameActionKey.EXTEND_DEADLINE: "can_extend_deadline",
        GameActionKey.PAUSE: "can_pause",
        GameActionKey.UNPAUSE: "can_unpause",
        GameActionKey.CLONE_TO_SANDBOX: "can_clone_to_sandbox",
        GameActionKey.LEAVE: "can_leave",
        GameActionKey.WITHDRAW: "can_withdraw",
        GameActionKey.DELETE: "can_delete",
    }

    def member_for(self, user):
        members = self.__dict__.setdefault("_member_for", {})
        if user.pk not in members:
            members[user.pk] = next(
                (
                    member
                    for member in self.members.all()
                    if member.user_id is not None and member.user_id == user.pk and member.replaced_by_id is None
                ),
                None,
            )
        return members[user.pk]

    def player_for(self, user):
        member = self.member_for(user)
        return member if member is not None and member.is_player else None

    def is_game_master(self, user):
        return self.game_master_id is not None and self.game_master_id == user.pk

    def can_manage(self, user):
        if self.admin_id != user.pk:
            return deny(DeniedReason.NOT_GAME_MANAGER)
        return ALLOW

    def can_join(self, user):
        if self.is_game_master(user):
            return deny(DeniedReason.GAME_MASTER_CANNOT_JOIN)
        if any(member.user_id == user.pk for member in self.members.all()):
            return deny(DeniedReason.ALREADY_MEMBER)
        if self.status != GameStatus.PENDING:
            return deny(DeniedReason.GAME_NOT_PENDING)
        return ALLOW

    def can_confirm_seat(self, user):
        if self.status != GameStatus.MUSTERING:
            return deny(DeniedReason.GAME_NOT_MUSTERING)
        player = self.player_for(user)
        if player is None:
            return deny(DeniedReason.NOT_PLAYER)
        if player.seat_confirmed:
            return deny(DeniedReason.SEAT_CONFIRMED)
        return ALLOW

    def can_edit_nation_preferences(self, user):
        if self.status != GameStatus.PENDING:
            return deny(DeniedReason.GAME_NOT_PENDING)
        if self.player_for(user) is None:
            return deny(DeniedReason.NOT_PLAYER)
        return ALLOW

    def can_assign_nations(self, user):
        if self.status != GameStatus.PENDING:
            return deny(DeniedReason.GAME_NOT_PENDING)
        if not self.is_game_master(user):
            return deny(DeniedReason.NOT_GAME_MASTER)
        return ALLOW

    def can_pause(self, user):
        return self.can_manage(user) and self.pause.available()

    def can_unpause(self, user):
        return self.can_manage(user) and self.unpause.available()

    def can_extend_deadline(self, user):
        return self.can_manage(user) and self.extend_deadline.available()

    def can_clone_to_sandbox(self, user):
        if self.status != GameStatus.ACTIVE:
            return deny(DeniedReason.GAME_NOT_ACTIVE)
        if self.sandbox:
            return deny(DeniedReason.SANDBOX_GAME)
        if self.player_for(user) is None:
            return deny(DeniedReason.NOT_PLAYER)
        return ALLOW

    def can_leave(self, user):
        if self.player_for(user) is None:
            return deny(DeniedReason.NOT_PLAYER)
        if self.status not in UNSTARTED:
            return deny(DeniedReason.GAME_STARTED)
        return ALLOW

    def can_withdraw(self, user):
        if self.status != GameStatus.ACTIVE:
            return deny(DeniedReason.GAME_NOT_ACTIVE)
        if self.sandbox:
            return deny(DeniedReason.SANDBOX_GAME)
        player = self.player_for(user)
        if player is None:
            return deny(DeniedReason.NOT_PLAYER)
        if player.eliminated or not player.occupied:
            return deny(DeniedReason.SEAT_VACATED)
        return ALLOW

    def can_delete(self, user):
        if self.sandbox:
            if self.member_for(user) is None:
                return deny(DeniedReason.NOT_PARTICIPANT)
            return ALLOW
        if not self.is_game_master(user):
            return deny(DeniedReason.NOT_GAME_MASTER)
        if self.status not in UNSTARTED:
            return deny(DeniedReason.GAME_STARTED)
        return ALLOW

    def can_create_channel(self, user):
        member = self.member_for(user)
        return can_create_channel(self, member if member is not None and not member.left_seat else None)

    def commitment_eligibility(self, user):
        if not user.is_authenticated:
            return None
        commitment = user.profile.commitment
        if commitment == Commitment.LOW and not self.private:
            return CommitmentEligibility.LOW_LOCKED
        if self.commitment_requirement == CommitmentRequirement.COMMITTED and commitment != Commitment.HIGH:
            return CommitmentEligibility.COMMITTED_LOCKED
        return CommitmentEligibility.ELIGIBLE

    def muster_status(self, user):
        if self.status != GameStatus.MUSTERING:
            return None
        player = self.player_for(user)
        if player is None:
            return None
        return MusterStatus.CONFIRMED if player.seat_confirmed else MusterStatus.CONFIRMATION_REQUIRED

    def current_phase_state_for(self, user):
        phase = self.current_phase
        if phase is None:
            return None
        return next((state for state in phase.phase_states.all() if state.member.user_id == user.pk), None)

    def phase_confirmed(self, user):
        state = self.current_phase_state_for(user)
        return state is not None and state.orders_confirmed

    def order_status(self, user):
        if self.sandbox or self.status != GameStatus.ACTIVE:
            return None
        state = self.current_phase_state_for(user)
        if state is None or not state.member.occupied:
            return None
        if state.orders_confirmed:
            return OrderStatus.ORDERS_SUBMITTED
        if not state.has_possible_orders:
            return OrderStatus.NO_ORDERS_REQUIRED
        if state.order_count == 0:
            return OrderStatus.ORDERS_REQUIRED
        if self.deadline_mode == DeadlineMode.FIXED_TIME:
            return OrderStatus.ORDERS_SUBMITTED
        return OrderStatus.ORDERS_NOT_CONFIRMED

    def member_status(self, user):
        if self.sandbox:
            return None
        member = self.player_for(user)
        if member is None:
            return []
        statuses = [MemberStatus.CIVIL_DISORDER] if member.civil_disorder else []
        if member.id in self.nmrd_member_ids:
            statuses.append(MemberStatus.NMR)
        return statuses

    def seat_for(self, user):
        if self.sandbox:
            return None
        return self.player_for(user)

    def seat_nation(self, user):
        seat = self.seat_for(user)
        return seat.nation.name if seat is not None and seat.nation is not None else None

    def my_state_kind(self, user):
        seat = self.seat_for(user)
        if self.sandbox:
            return MyGameStateKind.SANDBOX
        if self.is_finished or (seat is not None and seat.departure):
            return MyGameStateKind.FINISHED
        if self.status == GameStatus.PENDING:
            return MyGameStateKind.WAITING_FOR_PLAYERS
        if self.status == GameStatus.MUSTERING:
            if seat is None:
                return MyGameStateKind.MUSTERING
            if seat.mustered_at is None and not seat.is_bot:
                return MyGameStateKind.CONFIRM_SEAT
            return MyGameStateKind.SEAT_CONFIRMED
        if self.is_paused:
            return MyGameStateKind.PAUSED
        if seat is None:
            return MyGameStateKind.RESOLVING
        state = self.current_phase_state_for(user)
        orders_open = state is not None and state.has_possible_orders and not state.orders_confirmed
        if orders_open and state.order_count == 0:
            return MyGameStateKind.SUBMIT_ORDERS
        if self.pending_draw_vote:
            return MyGameStateKind.VOTE_ON_DRAW
        if orders_open:
            return MyGameStateKind.ORDERS_UNCONFIRMED
        if state is not None and state.orders_confirmed:
            return MyGameStateKind.ORDERS_CONFIRMED
        return MyGameStateKind.RESOLVING

    def my_deadline(self, user):
        kind = self.my_state_kind(user)
        if kind in (MyGameStateKind.CONFIRM_SEAT, MyGameStateKind.SEAT_CONFIRMED, MyGameStateKind.MUSTERING):
            return self.muster_deadline
        if kind in (
            MyGameStateKind.SUBMIT_ORDERS,
            MyGameStateKind.VOTE_ON_DRAW,
            MyGameStateKind.ORDERS_CONFIRMED,
            MyGameStateKind.RESOLVING,
        ):
            phase = self.current_phase
            return phase.scheduled_resolution if phase is not None else None
        return None

    def my_result(self, user):
        if self.status == GameStatus.ACTIVE:
            return MyGameResult.ONGOING
        if self.status == GameStatus.ABANDONED:
            return MyGameResult.ABANDONED
        victory = getattr(self, "victory", None)
        if victory is None:
            return None
        winners = victory.winners
        if len(winners) >= 2:
            return MyGameResult.DRAW
        seat = self.seat_for(user)
        if seat is not None and winners[0].id == seat.id:
            return MyGameResult.SOLO_VICTORY
        return MyGameResult.WON_BY

    def my_state(self, user):
        kind = self.my_state_kind(user)
        state = {"kind": kind, "deadline": self.my_deadline(user), "result": None, "winner": None, "departure": None}
        if kind == MyGameStateKind.FINISHED:
            seat = self.seat_for(user)
            state["result"] = self.my_result(user)
            state["departure"] = seat.departure if seat is not None else None
            if state["result"] == MyGameResult.WON_BY:
                state["winner"] = self.victory.winners[0].nation.name
        return state

    def my_section(self, user):
        kind = self.my_state_kind(user)
        if kind == MyGameStateKind.SANDBOX:
            return MyGamesSection.SANDBOX
        if kind == MyGameStateKind.FINISHED:
            return MyGamesSection.RECENTLY_FINISHED
        if self.seat_for(user) is None:
            return MyGamesSection.MANAGING
        if kind == MyGameStateKind.WAITING_FOR_PLAYERS:
            return MyGamesSection.PENDING
        if kind in (MyGameStateKind.CONFIRM_SEAT, MyGameStateKind.SUBMIT_ORDERS, MyGameStateKind.VOTE_ON_DRAW):
            return MyGamesSection.NEEDS_ATTENTION
        if kind == MyGameStateKind.SEAT_CONFIRMED:
            return MyGamesSection.MUSTERING
        return MyGamesSection.ACTIVE

    def my_sort_key(self, user):
        section = self.my_section(user)
        kind = self.my_state_kind(user)
        deadline = self.my_deadline(user)
        deadline_key = (deadline is None, deadline.timestamp() if deadline is not None else 0)
        if section == MyGamesSection.NEEDS_ATTENTION:
            section_key = (self.seat_for(user).id not in self.nmrd_member_ids,) + deadline_key
        elif section == MyGamesSection.MANAGING:
            section_key = (self.status == GameStatus.PENDING,) + deadline_key
        elif section == MyGamesSection.ACTIVE:
            rank = {MyGameStateKind.ORDERS_UNCONFIRMED: 0, MyGameStateKind.PAUSED: 2}.get(kind, 1)
            section_key = (rank,) + deadline_key
        elif section == MyGamesSection.MUSTERING:
            section_key = deadline_key
        elif section == MyGamesSection.PENDING:
            section_key = (-len(self.players),)
        elif section == MyGamesSection.RECENTLY_FINISHED:
            section_key = (-self.finished_at.timestamp() if self.finished_at else 0,)
        else:
            section_key = ()
        return section_key + (-self.created_at.timestamp(), self.id)


class MemberPolicy:
    def is_current_user(self, user):
        return self.user_id is not None and self.user_id == user.pk

    def is_masked_for(self, user):
        game = self.game
        if not game.anonymous or self.is_game_master or game.status == GameStatus.COMPLETED or self.is_bot:
            return False
        return not self.is_current_user(user)

    def visible_user_id(self, user):
        return None if self.is_masked_for(user) else self.user_id

    def visible_name(self, user):
        if self.is_masked_for(user):
            return "Anonymous"
        return self.user.profile.name if self.user is not None else "Deleted User"

    def visible_commitment(self, user):
        if self.is_masked_for(user) or self.user is None:
            return None
        return self.user.profile.commitment

    def visible_commitment_total(self, user):
        if self.is_masked_for(user) or self.user is None:
            return None
        return self.commitment_total

    def visible_commitment_band(self, user):
        total = self.visible_commitment_total(user)
        return CommitmentBand.for_total(total) if total is not None else None

    def is_game_creator(self, user):
        return not self.is_masked_for(user) and self.user_id is not None and self.user_id == self.game.created_by_id

    def is_admin(self, user):
        return not self.is_masked_for(user) and self.user_id is not None and self.user_id == self.game.admin_id

    def visible_nation_preference_ids(self, user):
        return self.nation_preference_ids if self.is_current_user(user) else []
