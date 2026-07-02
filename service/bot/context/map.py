from collections import deque
from typing import TypedDict

from common.constants import UnitType

from bot.types import ContextData, UnitDict, VariantProvinceDict

ARMY = "army"
FLEET = "fleet"


class GraphDict(TypedDict):
    edges: dict[str, dict[str, list[str]]]
    canonical: dict[str, str]


def build_graph(provinces: list[VariantProvinceDict]) -> GraphDict:
    canonical = {p["id"]: p.get("parent_id") or p["id"] for p in provinces}
    edge_sets: dict[str, dict[str, set[str]]] = {
        p["id"]: {ARMY: set(), FLEET: set()} for p in provinces if not p.get("parent_id")
    }
    for province in provinces:
        source = canonical[province["id"]]
        for adjacency in province.get("adjacencies", []):
            target = canonical.get(adjacency["to"])
            if target is None or target == source:
                continue
            if adjacency["pass"] in (ARMY, "both"):
                edge_sets[source][ARMY].add(target)
            if adjacency["pass"] in (FLEET, "both"):
                edge_sets[source][FLEET].add(target)
    edges = {
        province_id: {pass_type: sorted(targets) for pass_type, targets in sets.items()}
        for province_id, sets in edge_sets.items()
    }
    return {"edges": edges, "canonical": canonical}


def pass_type_for_unit(unit_type: str) -> str:
    return FLEET if unit_type == UnitType.FLEET else ARMY


def shortest_distances(graph: GraphDict, start: str, pass_type: str) -> dict[str, int]:
    start = graph["canonical"].get(start, start)
    distances = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbour in graph["edges"].get(current, {}).get(pass_type, []):
            if neighbour not in distances:
                distances[neighbour] = distances[current] + 1
                queue.append(neighbour)
    return distances


def nearest_enemy_units(
    data: ContextData, graph: GraphDict, unit: UnitDict, n: int = 3
) -> list[tuple[UnitDict, int]]:
    distances = shortest_distances(graph, unit["province"]["id"], pass_type_for_unit(unit["type"]))
    candidates = []
    for other in data["phase"].get("units", []):
        if other["nation"]["name"] == unit["nation"]["name"] or other.get("dislodged"):
            continue
        province_id = graph["canonical"].get(other["province"]["id"], other["province"]["id"])
        distance = distances.get(province_id)
        if distance is not None and distance >= 1:
            candidates.append((other, distance, province_id))
    candidates.sort(key=lambda c: (c[1], c[2]))
    return [(other, distance) for other, distance, _ in candidates[:n]]


def nearest_uncontrolled_supply_centers(
    data: ContextData, graph: GraphDict, unit: UnitDict, n: int = 3
) -> list[tuple[str, str | None, int]]:
    distances = shortest_distances(graph, unit["province"]["id"], pass_type_for_unit(unit["type"]))
    owners: dict[str, str] = {}
    for center in data["phase"].get("supply_centers", []):
        province_id = graph["canonical"].get(center["province"]["id"], center["province"]["id"])
        owners[province_id] = center["nation"]["name"]
    candidates = []
    for province in data["variant"].get("provinces", []):
        if not province.get("supply_center") or province.get("parent_id"):
            continue
        owner = owners.get(province["id"])
        if owner == unit["nation"]["name"]:
            continue
        distance = distances.get(province["id"])
        if distance is not None:
            candidates.append((province["id"], owner, distance))
    candidates.sort(key=lambda c: (c[2], c[0]))
    return candidates[:n]
