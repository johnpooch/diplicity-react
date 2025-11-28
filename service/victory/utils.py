def check_for_solo_winner(game, phase):
    required_sc_count = game.variant.solo_victory_sc_count

    sc_counts = {}
    for member in game.members.all():
        count = phase.supply_centers.filter(nation=member.nation).count()
        sc_counts[member] = count

    highest_count = 0
    leader = None

    for member, count in sc_counts.items():
        if count > highest_count:
            leader = member
            highest_count = count
        elif count == highest_count:
            leader = None

    if leader and highest_count >= required_sc_count:
        return leader

    return None
