from collections import deque

from select_orders.constants import PhaseType
from select_orders.exceptions import PromptError
from select_orders.prompt import render_part
from select_orders.prompt_data import prompt_data
from select_orders.types import Context, OrderOption, Unit
from select_orders.utils import current_nation

ADJECTIVES = {
    "Austria": "Austrian",
    "England": "English",
    "France": "French",
    "Germany": "German",
    "Italy": "Italian",
    "Russia": "Russian",
    "Turkey": "Turkish",
}


def join_and(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def listed(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def board_lines(context: Context, keep: set[str]) -> list[str]:
    return [
        render_part(
            "user.board.line",
            {
                **province,
                "adjacencies": ", ".join(
                    render_part("user.board.adjacency", adjacency) for adjacency in province["adjacencies"]
                ),
            },
        )
        for province in prompt_data(context)["board"]
        if province["id"] in keep
    ]


class Board:
    def __init__(self, context: Context):
        if context["phase"]["type"] != PhaseType.MOVEMENT:
            raise PromptError("prompt variants are written for movement phases only")
        self.context = context
        self.nation = current_nation(context)
        self.provinces = {province["id"]: province for province in context["provinces"]}
        self.units = [unit for unit in context["units"] if not unit["dislodged"]]
        self.unit_at = {self.parent(unit["province"]): unit for unit in self.units}
        self.owners = {center["province"]: center["nation"] for center in context["supply_centers"]}
        self.options = context["order_options"]

    def name(self, province_id: str) -> str:
        province = self.provinces.get(province_id)
        return province["name"] if province else province_id

    def parent(self, province_id: str) -> str:
        province = self.provinces.get(province_id)
        return (province and province["parent_id"]) or province_id

    def mine(self, unit: Unit) -> bool:
        return unit["nation"] == self.nation

    def own_units(self) -> list[Unit]:
        return [unit for unit in self.units if self.mine(unit)]

    def foreign_units(self) -> list[Unit]:
        return [unit for unit in self.units if not self.mine(unit)]

    def unit_for(self, province_id: str) -> Unit | None:
        return self.unit_at.get(self.parent(province_id))

    def unit_options(self, unit: Unit) -> list[OrderOption]:
        source = self.parent(unit["province"])
        return [option for option in self.options if option["source"] == source]

    def adjective(self, nation: str) -> str:
        return ADJECTIVES.get(nation, nation)

    def letter(self, unit: Unit) -> str:
        return unit["type"][0]

    def unit_name(self, unit: Unit) -> str:
        return f"{unit['type']} {self.name(unit['province'])}"

    def short(self, unit: Unit) -> str:
        return f"{self.letter(unit)} {self.name(unit['province'])}"

    def owned_short(self, unit: Unit) -> str:
        return f"your {self.short(unit)}" if self.mine(unit) else f"{unit['nation']} {self.short(unit)}"

    def unit_line(self, unit: Unit) -> str:
        return render_part(
            "user.units.line",
            {
                "type": unit["type"],
                "province": self.name(unit["province"]),
                "nation": unit["nation"],
                "mine": self.mine(unit),
                "dislodged": unit["dislodged"],
            },
        )

    def fleet_name(self, unit: Unit) -> str:
        return self.unit_name(unit) if self.mine(unit) else f"{unit['nation']} {self.unit_name(unit)}"

    def supply_centre_note(self, province_id: str) -> str | None:
        if province_id not in self.owners:
            return None
        owner = self.owners[province_id]
        if owner is None:
            return "SC, unowned"
        return "your SC" if owner == self.nation else f"SC, {owner}"

    def occupancy(self, province_id: str) -> str:
        unit = self.unit_for(province_id)
        return f"occupied by {self.owned_short(unit)}" if unit else "empty"

    def neighbours(self, node: str, unit_type: str) -> list[str]:
        province = self.provinces.get(node)
        if province is None:
            return []
        if unit_type == "Army":
            province = self.provinces[self.parent(node)]
        allows = unit_type.lower()
        return [adjacency["to"] for adjacency in province["adjacencies"] if allows in adjacency["allows"]]

    def reach(self, node: str, unit_type: str) -> list[str]:
        seen: list[str] = []
        for neighbour in self.neighbours(node, unit_type):
            if self.parent(neighbour) not in seen:
                seen.append(self.parent(neighbour))
        return seen

    def can_move(self, unit: Unit, province_id: str) -> bool:
        return province_id in self.reach(unit["province"], unit["type"])

    def movers(self, province_id: str, exclude: list[Unit] | None = None) -> list[Unit]:
        skipped = [*(exclude or []), self.unit_for(province_id)]
        return [
            unit
            for unit in self.foreign_units()
            if not any(unit is other for other in skipped) and self.can_move(unit, province_id)
        ]

    def convoy_targets(self, unit: Unit) -> list[str]:
        return [option["target"] for option in self.unit_options(unit) if option["order_type"] == "MoveViaConvoy"]

    def _fleet_seas(self, avoid: str | None) -> set[str]:
        return {
            self.parent(unit["province"])
            for unit in self.units
            if unit["type"] == "Fleet"
            and self.provinces.get(self.parent(unit["province"]), {}).get("type") == "sea"
            and self.parent(unit["province"]) != avoid
        }

    def _touches(self, sea: str, province_id: str) -> bool:
        return province_id in self.reach(sea, "Fleet")

    def _sea_path(self, origin: str, done, seas: set[str]) -> list[str] | None:
        queue = deque([[sea] for sea in self.neighbours(origin, "Fleet") if sea in seas])
        seen = {path[0] for path in queue}
        while queue:
            path = queue.popleft()
            if done(path[-1]):
                return path
            for neighbour in self.neighbours(path[-1], "Fleet"):
                if neighbour in seas and neighbour not in seen:
                    seen.add(neighbour)
                    queue.append([*path, neighbour])
        return None

    def convoy_route(self, army: str, target: str, avoid: str | None = None) -> list[str] | None:
        seas = self._fleet_seas(avoid)
        return self._sea_path(army, lambda sea: self._touches(sea, target), seas)

    def convoy_route_through(self, army: str, target: str, fleet: str) -> list[str] | None:
        seas = self._fleet_seas(None)
        to_fleet = self._sea_path(army, lambda sea: sea == fleet, seas)
        if to_fleet is None:
            return None
        if self._touches(fleet, target):
            return to_fleet
        onward = self._sea_path(fleet, lambda sea: self._touches(sea, target), seas)
        return None if onward is None else [*to_fleet, *onward]

    def route_fleets(self, route: list[str]) -> list[Unit]:
        return [self.unit_at[sea] for sea in route]

    def moves_away(self, unit: Unit, limit: int) -> dict[str, int]:
        distances = {self.parent(unit["province"]): 0}
        seen = {unit["province"]}
        frontier = [unit["province"]]
        for step in range(1, limit + 1):
            reached = []
            for node in frontier:
                neighbours = self.neighbours(node, unit["type"])
                if step == 1 and unit["type"] == "Army":
                    neighbours = [*neighbours, *self.convoy_targets(unit)]
                for neighbour in neighbours:
                    if neighbour not in seen:
                        seen.add(neighbour)
                        reached.append(neighbour)
                        distances.setdefault(self.parent(neighbour), step)
            frontier = reached
        return distances

    def distances(self, units: list[Unit], limit: int) -> dict[str, int]:
        nearest: dict[str, int] = {}
        for unit in units:
            for province_id, distance in self.moves_away(unit, limit).items():
                nearest[province_id] = min(distance, nearest.get(province_id, distance))
        return nearest

    def near(self, limit: int) -> set[str]:
        return set(self.distances(self.own_units(), limit))

    def near_province_ids(self, limit: int) -> list[str]:
        near = self.near(limit)
        return [province["id"] for province in self.context["provinces"] if self.parent(province["id"]) in near]

    def near_foreign_units(self, limit: int) -> list[Unit]:
        near = self.near(limit)
        return [unit for unit in self.foreign_units() if self.parent(unit["province"]) in near]

    def centre_names(self, nation: str | None) -> list[str]:
        centers = self.context["supply_centers"]
        return [self.name(center["province"]) for center in centers if center["nation"] == nation]

    def powers_summary(self) -> str:
        lines = ["Powers (supply centres / units):"]
        for member in self.context["members"]:
            nation = member["nation"]
            centres = self.centre_names(nation)
            units = [unit for unit in self.units if unit["nation"] == nation]
            you = " [you]" if nation == self.nation else ""
            lines.append(
                f"  {nation}{you}: {plural(len(centres), 'SC')} ({', '.join(centres)}) / {plural(len(units), 'unit')}"
            )
        unowned = self.centre_names(None)
        if unowned:
            lines.append(f"  Unowned: {plural(len(unowned), 'SC')} ({', '.join(unowned)})")
        return "\n".join(lines)

    def move_note(self, province_id: str) -> str:
        parts = [self.supply_centre_note(province_id), self.occupancy(province_id)]
        movers = listed([self.owned_short(unit) for unit in self.movers(province_id)])
        parts.append(f"other powers that can also move here: {movers}")
        return "; ".join(part for part in parts if part)
