import random


def assign_nations(seed, members, nations):
    taken = {m.nation_id for m in members if m.nation_id is not None}
    available = {n.id: n for n in nations if n.id not in taken}
    result = {m.id: m.nation for m in members if m.nation_id is not None}

    unassigned = [m for m in members if m.nation_id is None]
    rng = random.Random(seed)
    rng.shuffle(unassigned)

    for member in unassigned:
        choice = None
        for preference in member.nation_preferences.all():
            if preference.nation_id in available:
                choice = available.pop(preference.nation_id)
                break
        if choice is None:
            choice = available.pop(rng.choice(sorted(available)))
        result[member.id] = choice

    return result
