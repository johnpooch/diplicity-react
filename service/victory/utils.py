from fractions import Fraction

from django.db.models import Count


def check_for_solo_winner(game, phase):
    counts_by_nation = {
        row["nation"]: row["count"]
        for row in phase.supply_centers.values("nation").annotate(count=Count("id"))
    }

    ratios = {}
    for member in game.members.players().not_replaced().select_related("nation"):
        target = game.variant.solo_victory_supply_centers_for(member.nation.nation_id)
        if target is None:
            continue
        count = counts_by_nation.get(member.nation_id, 0)
        if count >= target:
            ratios[member] = Fraction(count, target)

    if not ratios:
        return None

    highest_ratio = max(ratios.values())
    leaders = [member for member, ratio in ratios.items() if ratio == highest_ratio]
    if len(leaders) == 1:
        return leaders[0]

    return None
