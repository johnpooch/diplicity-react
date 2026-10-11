from collections import defaultdict
from datetime import timedelta

from django.db.models import F, Q
from django.db.models.functions import Coalesce, Least
from django.utils import timezone

from common.constants import GameStatus, MemberDeparture, MyGameResult, MyGamesSection, MyGameStateKind
from draw_proposal.models import DrawVote
from member.models import Member

from .models import Game


class _FinishedRows:
    def __init__(self, seats, load_rows):
        self._seats = seats
        self._load_rows = load_rows

    def count(self):
        return self._seats.count()

    def __getitem__(self, page):
        return self._load_rows(list(self._seats[page]))


class MyGamesService:
    def __init__(self, user):
        self.user = user

    def current(self):
        games = self._current_games()
        Game.objects.hydrate_list_phases(games)
        Game.objects.hydrate_total_unread_counts(games, self.user)
        seats = self._seats(games)
        pending_draw_vote_game_ids = self._pending_draw_vote_game_ids(games)

        rows_by_section = defaultdict(list)
        for game in games:
            seat = seats.get(game.id)
            if not self._in_current(game, seat):
                continue
            kind = self._state_kind(game, seat, game.id in pending_draw_vote_game_ids)
            section = self._section(seat, kind)
            row = self._row(game, seat, kind)
            rows_by_section[section].append((self._sort_key(game, seat, kind, section), row))

        return {
            "sections": [
                {
                    "key": section,
                    "games": [row for _, row in sorted(rows_by_section[section], key=lambda pair: pair[0])],
                }
                for section, _ in MyGamesSection.SECTION_CHOICES
                if rows_by_section[section]
            ]
        }

    def finished(self):
        return _FinishedRows(self._finished_seats(), self._finished_rows)

    def _finished_seats(self):
        return (
            Member.objects.filter(user=self.user, game__sandbox=False)
            .annotate(departed_at=Least("eliminated_at", "civil_disorder_at", "removed_at", "withdrawn_at"))
            .filter(
                Q(game__status__in=(GameStatus.COMPLETED, GameStatus.ABANDONED))
                | Q(game__status=GameStatus.ACTIVE, departed_at__isnull=False)
            )
            .annotate(ended_at=Coalesce("departed_at", "game__finished_at"))
            .select_related("nation")
            .order_by(F("ended_at").desc(nulls_last=True), "-game__created_at", "-game_id")
        )

    def _finished_rows(self, members):
        games_by_id = Game.objects.with_list_data().in_bulk([member.game_id for member in members])
        games = [games_by_id[member.game_id] for member in members]
        Game.objects.hydrate_list_phases(games)
        Game.objects.hydrate_total_unread_counts(games, self.user)
        return [
            self._row(game, None if member.is_game_master else member, MyGameStateKind.FINISHED)
            for member, game in zip(members, games)
        ]

    def _current_games(self):
        recently_finished_cutoff = timezone.now() - timedelta(days=3)
        return list(
            Game.objects.filter_mine(self.user)
            .with_my_games_data()
            .filter(
                Q(status__in=(GameStatus.PENDING, GameStatus.MUSTERING, GameStatus.ACTIVE))
                | Q(sandbox=True)
                | Q(
                    status__in=(GameStatus.COMPLETED, GameStatus.ABANDONED),
                    finished_at__gte=recently_finished_cutoff,
                )
            )
        )

    def _seats(self, games):
        members = Member.objects.filter(game_id__in=[game.id for game in games], user=self.user).select_related(
            "nation", "user__profile"
        )
        sandbox_game_ids = {game.id for game in games if game.sandbox}
        seats = {}
        for member in members:
            if member.game_id in sandbox_game_ids or member.is_game_master or member.game_id in seats:
                continue
            seats[member.game_id] = member
        return seats

    def _pending_draw_vote_game_ids(self, games):
        current_phase_ids = [game.current_phase.id for game in games if game.current_phase is not None]
        if not current_phase_ids:
            return set()
        return set(
            DrawVote.objects.filter(
                member__user=self.user,
                accepted__isnull=True,
                proposal__cancelled=False,
                proposal__phase_id__in=current_phase_ids,
            )
            .exclude(proposal__votes__accepted=False)
            .values_list("proposal__game_id", flat=True)
        )

    def _in_current(self, game, seat):
        if game.sandbox:
            return True
        if seat is None or seat.departure is None:
            return True
        return seat.departure == MemberDeparture.ELIMINATED and game.status != GameStatus.ACTIVE

    def _phase_state(self, game, seat):
        current_phase = game.current_phase
        if seat is None or current_phase is None:
            return None
        return next(
            (phase_state for phase_state in current_phase.phase_states.all() if phase_state.member_id == seat.id),
            None,
        )

    def _state_kind(self, game, seat, has_pending_draw_vote):
        if game.sandbox:
            return MyGameStateKind.SANDBOX
        if game.status in (GameStatus.COMPLETED, GameStatus.ABANDONED) or (seat is not None and seat.departure):
            return MyGameStateKind.FINISHED
        if seat is None:
            if game.status == GameStatus.PENDING:
                return MyGameStateKind.WAITING_FOR_PLAYERS
            if game.status == GameStatus.MUSTERING:
                return MyGameStateKind.MUSTERING
            if game.is_paused:
                return MyGameStateKind.PAUSED
            return MyGameStateKind.RESOLVING
        if game.status == GameStatus.PENDING:
            return MyGameStateKind.WAITING_FOR_PLAYERS
        if game.status == GameStatus.MUSTERING:
            if seat.mustered_at is None and not seat.is_bot:
                return MyGameStateKind.CONFIRM_SEAT
            return MyGameStateKind.SEAT_CONFIRMED
        if game.is_paused:
            return MyGameStateKind.PAUSED
        phase_state = self._phase_state(game, seat)
        orders_open = phase_state is not None and phase_state.has_possible_orders and not phase_state.orders_confirmed
        if orders_open and phase_state.order_count == 0:
            return MyGameStateKind.SUBMIT_ORDERS
        if has_pending_draw_vote:
            return MyGameStateKind.VOTE_ON_DRAW
        if orders_open:
            return MyGameStateKind.ORDERS_UNCONFIRMED
        if phase_state is not None and phase_state.orders_confirmed:
            return MyGameStateKind.ORDERS_CONFIRMED
        return MyGameStateKind.RESOLVING

    def _section(self, seat, kind):
        if kind == MyGameStateKind.SANDBOX:
            return MyGamesSection.SANDBOX
        if kind == MyGameStateKind.FINISHED:
            return MyGamesSection.RECENTLY_FINISHED
        if seat is None:
            return MyGamesSection.MANAGING
        if kind == MyGameStateKind.WAITING_FOR_PLAYERS:
            return MyGamesSection.PENDING
        if kind in (MyGameStateKind.CONFIRM_SEAT, MyGameStateKind.SUBMIT_ORDERS, MyGameStateKind.VOTE_ON_DRAW):
            return MyGamesSection.NEEDS_ATTENTION
        if kind == MyGameStateKind.SEAT_CONFIRMED:
            return MyGamesSection.MUSTERING
        return MyGamesSection.ACTIVE

    def _deadline(self, game, kind):
        if kind in (MyGameStateKind.CONFIRM_SEAT, MyGameStateKind.SEAT_CONFIRMED, MyGameStateKind.MUSTERING):
            return game.muster_deadline
        if kind in (
            MyGameStateKind.SUBMIT_ORDERS,
            MyGameStateKind.VOTE_ON_DRAW,
            MyGameStateKind.ORDERS_CONFIRMED,
            MyGameStateKind.RESOLVING,
        ):
            current_phase = game.current_phase
            return current_phase.scheduled_resolution if current_phase is not None else None
        return None

    def _result(self, game, seat):
        if game.status == GameStatus.ACTIVE:
            return MyGameResult.ONGOING
        if game.status == GameStatus.ABANDONED:
            return MyGameResult.ABANDONED
        victory = getattr(game, "victory", None)
        if victory is None:
            return None
        winners = list(victory.members.all())
        if len(winners) >= 2:
            return MyGameResult.DRAW
        if seat is not None and winners[0].id == seat.id:
            return MyGameResult.SOLO_VICTORY
        return MyGameResult.WON_BY

    def _state(self, game, seat, kind):
        state = {
            "kind": kind,
            "deadline": self._deadline(game, kind),
            "result": None,
            "winner": None,
            "departure": None,
        }
        if kind == MyGameStateKind.FINISHED:
            state["result"] = self._result(game, seat)
            state["departure"] = seat.departure if seat is not None else None
            if state["result"] == MyGameResult.WON_BY:
                state["winner"] = game.victory.members.all()[0].nation.name
        return state

    def _seat_counts(self, game):
        if game.status == GameStatus.PENDING:
            filled = len(game.members.all())
        elif game.status == GameStatus.MUSTERING:
            filled = len([member for member in game.members.all() if member.mustered_at is not None or member.is_bot])
        else:
            return None
        total = len([nation for nation in game.variant.nations.all() if not nation.non_playable])
        return {"filled": filled, "total": total}

    def _row(self, game, seat, kind):
        current_phase = game.current_phase
        return {
            "id": game.id,
            "name": game.name,
            "status": game.status,
            "variant_id": game.variant_id,
            "sandbox": game.sandbox,
            "current_phase_id": current_phase.id if current_phase is not None else None,
            "current_phase": current_phase,
            "nation": seat.nation.name if seat is not None and seat.nation is not None else None,
            "seats": self._seat_counts(game),
            "unread_count": game.total_unread_message_count,
            "state": self._state(game, seat, kind),
        }

    def _sort_key(self, game, seat, kind, section):
        deadline = self._deadline(game, kind)
        deadline_key = (deadline is None, deadline.timestamp() if deadline is not None else 0)
        if section == MyGamesSection.NEEDS_ATTENTION:
            section_key = (seat.id not in game.nmrd_member_ids,) + deadline_key
        elif section == MyGamesSection.MANAGING:
            section_key = (game.status == GameStatus.PENDING,) + deadline_key
        elif section == MyGamesSection.ACTIVE:
            rank = {MyGameStateKind.ORDERS_UNCONFIRMED: 0, MyGameStateKind.PAUSED: 2}.get(kind, 1)
            section_key = (rank,) + deadline_key
        elif section == MyGamesSection.MUSTERING:
            section_key = deadline_key
        elif section == MyGamesSection.PENDING:
            section_key = (-len(game.members.all()),)
        elif section == MyGamesSection.RECENTLY_FINISHED:
            section_key = (-game.finished_at.timestamp(),)
        else:
            section_key = ()
        return section_key + (-game.created_at.timestamp(), game.id)
