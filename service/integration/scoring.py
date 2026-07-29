from dataclasses import dataclass

from bot_profile.models import BotProfile

HUMAN_KIND = "human"


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
    for member in phase.game.members.select_related("nation"):
        if member.nation is None or member.user_id is None:
            continue
        profile = BotProfile.objects.filter(user_id=member.user_id).first()
        kinds[member.nation.name] = profile.kind if profile else HUMAN_KIND

    scores = {nation: count**2 for nation, count in centers.items()}
    cohorts: dict[str, int] = {}
    for nation, score in scores.items():
        kind = kinds.get(nation, HUMAN_KIND)
        cohorts[kind] = cohorts.get(kind, 0) + score

    return GameScore(
        centers=centers,
        scores=scores,
        kinds=kinds,
        cohorts=cohorts,
        total=sum(scores.values()),
    )
