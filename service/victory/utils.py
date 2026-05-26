from django.db.models import Count


def check_for_solo_winner(game, phase):
    required_sc_count = game.variant.solo_victory_supply_centers

    counts_by_nation = {
        row["nation"]: row["count"]
        for row in phase.supply_centers.values("nation").annotate(count=Count("id"))
    }

    highest_count = 0
    leader = None

    for member in game.members.all():
        count = counts_by_nation.get(member.nation_id, 0)
        if count > highest_count:
            leader = member
            highest_count = count
        elif count == highest_count:
            leader = None

    if leader and highest_count >= required_sc_count:
        return leader

    return None
