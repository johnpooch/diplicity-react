from django.contrib.auth import get_user_model

from common.constants import GameStatus
from member.models import Member
from phase.models import PhaseState

User = get_user_model()

RELIABILITY_GAME_WINDOW = 10
RELIABLE_NMR_THRESHOLD = 0.1
RELIABLE_CD_THRESHOLD = 0.1


def get_player_stats(user):
    completed_members = (
        Member.objects.filter(
            user=user,
            game__status=GameStatus.COMPLETED,
            game__sandbox=False,
            kicked=False,
        )
        .select_related("game")
        .order_by("-game__finished_at")
    )

    total_games = completed_members.count()
    solo_wins = completed_members.filter(won=True).count()
    draws = completed_members.filter(drew=True).count()
    losses = total_games - solo_wins - draws

    last_n_members = list(completed_members[:RELIABILITY_GAME_WINDOW])
    last_n_member_ids = [m.id for m in last_n_members]

    phase_states_with_orders = PhaseState.objects.filter(
        member_id__in=last_n_member_ids,
        has_possible_orders=True,
        phase__status="completed",
    )
    total_phases = phase_states_with_orders.count()
    nmr_phases = phase_states_with_orders.filter(
        orders_outcome=PhaseState.OrdersOutcome.NMR
    ).count()
    nmr_rate = nmr_phases / total_phases if total_phases > 0 else 0.0

    cd_count = sum(1 for m in last_n_members if m.civil_disorder)
    cd_rate = cd_count / len(last_n_members) if last_n_members else 0.0

    if total_games < RELIABILITY_GAME_WINDOW:
        reliability_tier = "new"
    elif nmr_rate <= RELIABLE_NMR_THRESHOLD and cd_rate <= RELIABLE_CD_THRESHOLD:
        reliability_tier = "reliable"
    else:
        reliability_tier = None

    return {
        "total_games": total_games,
        "solo_wins": solo_wins,
        "draws": draws,
        "losses": losses,
        "nmr_rate": round(nmr_rate, 4),
        "cd_rate": round(cd_rate, 4),
        "reliability_tier": reliability_tier,
    }
