from collections import Counter

from common.constants import ProvinceType, UnitType
from harness.types import Context

from dumbbot.weights import SIZE_COEFFICIENT, SIZE_CONSTANT, SIZE_SQUARE_COEFFICIENT

ALLOWS_TO_UNIT_TYPE = {
    "army": UnitType.ARMY,
    "fleet": UnitType.FLEET,
}


class Board:
    def __init__(self, context: Context, nation: str):
        self.nation = nation
        provinces = context["provinces"]
        self.parent = {province["id"]: province["parent_id"] or province["id"] for province in provinces}
        self.adjacencies = {province["id"]: province["adjacencies"] for province in provinces}
        self.province_ids = [province["id"] for province in provinces if province["parent_id"] is None]

        coast_parents = {province["parent_id"] for province in provinces if province["parent_id"]}
        self.placements = set()
        for province in provinces:
            if province["type"] in (ProvinceType.LAND, ProvinceType.COASTAL):
                self.placements.add((UnitType.ARMY, province["id"]))
            if province["type"] in (ProvinceType.SEA, ProvinceType.NAMED_COAST):
                self.placements.add((UnitType.FLEET, province["id"]))
            if province["type"] == ProvinceType.COASTAL and province["id"] not in coast_parents:
                self.placements.add((UnitType.FLEET, province["id"]))

        self.movers_into = {province_id: set() for province_id in self.province_ids}
        for province in provinces:
            for adjacency in province["adjacencies"]:
                destination = self.parent.get(adjacency["to"])
                if destination is None:
                    continue
                for allowed in adjacency["allows"]:
                    key = (ALLOWS_TO_UNIT_TYPE[allowed], province["id"])
                    if key in self.placements:
                        self.movers_into[destination].add(key)

        self.standing_units = [unit for unit in context["units"] if not unit["dislodged"]]
        self.dislodged_units = [unit for unit in context["units"] if unit["dislodged"]]

        adjacent_units = {province_id: {} for province_id in self.province_ids}
        for unit in self.standing_units:
            for destination in self.reachable_provinces(unit["province"], unit["type"]):
                adjacent_units[destination].setdefault(unit["nation"], set()).add(unit["province"])

        self.strength = {}
        self.competition = {}
        for province_id in self.province_ids:
            counts = adjacent_units[province_id]
            self.strength[province_id] = len(counts.get(nation, ()))
            self.competition[province_id] = max(
                (len(units) for other, units in counts.items() if other != nation),
                default=0,
            )

        center_counts = Counter(
            center["nation"] for center in context["supply_centers"] if center["nation"] is not None
        )
        sizes = {
            owner: SIZE_SQUARE_COEFFICIENT * count**2 + SIZE_COEFFICIENT * count + SIZE_CONSTANT
            for owner, count in center_counts.items()
        }

        self.attack = {province_id: 0 for province_id in self.province_ids}
        self.defense = {province_id: 0 for province_id in self.province_ids}
        for center in context["supply_centers"]:
            province_id = center["province"]
            if center["nation"] != nation:
                self.attack[province_id] = sizes.get(center["nation"], SIZE_CONSTANT)
            else:
                self.defense[province_id] = max(
                    (
                        sizes.get(other, SIZE_CONSTANT)
                        for other, units in adjacent_units[province_id].items()
                        if other != nation and units
                    ),
                    default=0,
                )

    def reachable_provinces(self, location, unit_type):
        destinations = set()
        for adjacency in self.adjacencies.get(location, []):
            if any(ALLOWS_TO_UNIT_TYPE[allowed] == unit_type for allowed in adjacency["allows"]):
                parent = self.parent.get(adjacency["to"])
                if parent is not None:
                    destinations.add(parent)
        return destinations
