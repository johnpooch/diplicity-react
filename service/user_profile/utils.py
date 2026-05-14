from common.constants import (
    GameStatus,
    MemberOutcomeState,
    RELIABILITY_WINDOW_SIZE,
)
from member.models import Member
from user_profile.models import UserProfile


def backfill_reliability_data():
    from game.models import Game
    from member.utils import classify_outcomes_for_finished_game

    finished_games = Game.objects.filter(
        status__in=GameStatus.FINISHED_STATUSES,
        sandbox=False,
    )
    for game in finished_games:
        classify_outcomes_for_finished_game(game)


def recompute_reliability_counters(user_id):
    profile = UserProfile.objects.filter(user_id=user_id).first()
    if profile is None:
        return

    finished_qs = (
        Member.objects.filter(
            user_id=user_id,
            outcome_state__isnull=False,
            game__status__in=GameStatus.FINISHED_STATUSES,
            game__private=False,
            game__sandbox=False,
        )
        .order_by("-game__updated_at", "-game_id")
    )

    games_finished = finished_qs.count()
    recent_outcomes = list(
        finished_qs.values_list("outcome_state", flat=True)[:RELIABILITY_WINDOW_SIZE]
    )
    games_abandoned_recent = sum(
        1 for state in recent_outcomes if state == MemberOutcomeState.ABANDONED
    )

    profile.games_finished = games_finished
    profile.games_abandoned_recent = games_abandoned_recent
    profile.save(update_fields=["games_finished", "games_abandoned_recent", "updated_at"])
