from dataclasses import dataclass

from common.constants import UserKind


@dataclass
class GameScore:
    centers: dict[str, int]
    scores: dict[str, int]
    kinds: dict[str, str]
    cohorts: dict[str, int]
    total: int


def sum_of_squares(phase):
    centers: dict[str, int] = {}
    for supply_center in phase.supply_centers.select_related("nation"):
        centers[supply_center.nation.name] = centers.get(supply_center.nation.name, 0) + 1

    kinds: dict[str, str] = {}
    for member in phase.game.members.select_related("nation", "user__profile"):
        if member.nation is None or member.user_id is None:
            continue
        kinds[member.nation.name] = member.user.profile.kind

    scores = {nation: count**2 for nation, count in centers.items()}
    cohorts: dict[str, int] = {}
    for nation, score in scores.items():
        kind = kinds.get(nation, UserKind.HUMAN)
        cohorts[kind] = cohorts.get(kind, 0) + score

    return GameScore(
        centers=centers,
        scores=scores,
        kinds=kinds,
        cohorts=cohorts,
        total=sum(scores.values()),
    )
