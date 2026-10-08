from math import prod

from engine.exceptions import UnknownVariantError
from engine.positions import Board
from engine.rules import load_variant
from harvest.exceptions import HarvestError
from select_orders.constants import PhaseType
from select_orders.fixtures import full_option, validate_fixture
from select_orders.options import option_id
from select_orders.schema import FIXTURE_SCHEMA_VERSION
from select_orders.types import Fixture

COMPLETED = "completed"
SUCCEEDED = "OK"
OPTION_FIELDS = ("target", "aux", "unit_type", "named_coast")
UNORDERED_TYPES = ("Hold", "Disband")


def _by_phase(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["phase"], []).append(row)
    return grouped


def _unit(row):
    unit = {"type": row["type"], "nation": row["nation"], "province": row["province"]}
    if row["dislodged"]:
        unit["dislodged"] = True
    if row["dislodged_from"] is not None:
        unit["dislodged_from"] = row["dislodged_from"]
    return unit


def _option(order):
    option = {"source": order["source"], "order_type": order["order_type"]}
    if order["order_type"] in UNORDERED_TYPES:
        return option
    option.update({key: order[key] for key in OPTION_FIELDS if order[key] is not None})
    return option


def _phase(phase):
    return {"season": phase["season"], "year": phase["year"], "type": phase["type"]}


def _label(phase):
    return f"{phase['season']} {phase['year']} {phase['type']} (phase {phase['id']})"


class Harvest:
    def __init__(self, snapshot: dict, *, harvested_at: str):
        self.harvested_at = harvested_at
        self.games = {game["id"]: game for game in snapshot["games"]}
        self.phases = {phase["id"]: phase for phase in snapshot["phases"]}
        self.by_ordinal = {(phase["game"], phase["ordinal"]): phase for phase in snapshot["phases"]}
        self.units = _by_phase(snapshot["units"])
        self.supply_centers = _by_phase(snapshot["supply_centers"])
        self.orders = _by_phase(snapshot["orders"])
        self.bots = {(player["phase"], player["nation"]): player["was_bot"] for player in snapshot["players"]}

    def phase_ids(self) -> list[int]:
        return [phase["id"] for phase in self.phases.values() if phase["status"] == COMPLETED]

    def legal_options(self, phase_id: int) -> dict[str, list[dict]]:
        board, state = self._position(self._phase_row(phase_id))
        return board.options_by_nation(state)

    def fixtures(self, phase_id: int, nations=None) -> list[Fixture]:
        phase = self._phase_row(phase_id)
        if phase["status"] != COMPLETED:
            raise HarvestError(f"{_label(phase)} is not completed, so it has no final orders")
        board, state = self._position(phase)
        options = board.options_by_nation(state)
        actual_orders = self._actual_orders(phase, options)
        outcome, following = board.outcome(state, actual_orders)
        self._check_resolutions(phase, outcome)
        self._check_next_phase(phase, outcome, following)
        return [
            self._fixture(phase, nation, options[nation], actual_orders, outcome)
            for nation in sorted(options)
            if nations is None or nation in nations
        ]

    def _phase_row(self, phase_id):
        phase = self.phases.get(phase_id)
        if phase is None:
            raise HarvestError(f"snapshot has no phase {phase_id}")
        return phase

    def _position(self, phase):
        try:
            variant = load_variant(self.games[phase["game"]]["variant"])
        except UnknownVariantError as e:
            raise HarvestError(str(e)) from e
        board = Board(variant)
        state = board.game_state(
            _phase(phase),
            self._units(phase["id"]),
            self._supply_centers(phase["id"]),
            phase["contested_provinces"],
        )
        return board, state

    def _units(self, phase_id):
        return sorted(
            (_unit(row) for row in self.units.get(phase_id, [])),
            key=lambda unit: (unit["province"], unit.get("dislodged", False)),
        )

    def _supply_centers(self, phase_id):
        return sorted(
            ({"nation": row["nation"], "province": row["province"]} for row in self.supply_centers.get(phase_id, [])),
            key=lambda center: center["province"],
        )

    def _actual_orders(self, phase, options):
        nations = {unit["nation"] for unit in self._units(phase["id"])} | set(options)
        actual = {nation: [] for nation in sorted(nations)}
        for order in self.orders.get(phase["id"], []):
            legal = {option_id(full_option(option)): option for option in options.get(order["nation"], [])}
            chosen = option_id(full_option(_option(order)))
            if chosen not in legal:
                raise HarvestError(f"{_label(phase)}: {order['nation']} order {chosen} is not a legal option")
            actual.setdefault(order["nation"], []).append(legal[chosen])
        return actual

    def _check_resolutions(self, phase, outcome):
        results = {(r["nation"], r["source"]): r["result"] for r in outcome["resolutions"]}
        for order in self.orders.get(phase["id"], []):
            stored = order["resolution"]
            computed = results.get((order["nation"], order["source"]))
            if stored is not None and (stored == SUCCEEDED) != (computed == SUCCEEDED):
                raise HarvestError(
                    f"{_label(phase)}: {order['nation']} {order['source']} resolved {stored} in the game "
                    f"but {computed} on replay"
                )

    def _check_next_phase(self, phase, outcome, following):
        stored = self.by_ordinal.get((phase["game"], phase["ordinal"] + 1))
        if stored is None:
            return
        same = _phase(stored) == following["phase"]
        skipped = following["phase"]["type"] == PhaseType.RETREAT and not any(
            unit["dislodged"] for unit in following["units"]
        )
        if not same and not skipped:
            return
        if self._units(stored["id"]) != outcome["units"]:
            raise HarvestError(f"{_label(phase)}: replayed units differ from the stored {_label(stored)}")
        if same and self._supply_centers(stored["id"]) != outcome["supply_centers"]:
            raise HarvestError(f"{_label(phase)}: replayed supply centres differ from the stored {_label(stored)}")

    def _fixture(self, phase, nation, options, actual_orders, outcome) -> Fixture:
        game = self.games[phase["game"]]
        units = self._units(phase["id"])
        supply_centers = self._supply_centers(phase["id"])
        counts = {}
        for option in options:
            counts[option["source"]] = counts.get(option["source"], 0) + 1
        fixture: Fixture = {
            "schema_version": FIXTURE_SCHEMA_VERSION,
            "id": f"{game['id']}_p{phase['ordinal']}_{nation.lower()}",
            "provenance": {
                "source": "harvested",
                "game_id": game["id"],
                "phase_id": phase["id"],
                "phase_ordinal": phase["ordinal"],
                "harvested_at": self.harvested_at,
                "press_type": game["press_type"],
                "was_bot": self.bots.get((phase["id"], nation), False),
            },
            "variant": game["variant"],
            "nation": nation,
            "phase": _phase(phase),
            "units": units,
            "supply_centers": supply_centers,
            "order_options": options,
        }
        if phase["contested_provinces"]:
            fixture["contested_provinces"] = phase["contested_provinces"]
        if phase["type"] == PhaseType.ADJUSTMENT:
            owned = sum(1 for center in supply_centers if center["nation"] == nation)
            fixture["max_orders"] = abs(owned - sum(1 for unit in units if unit["nation"] == nation))
        fixture["decision_richness"] = prod(counts.values())
        fixture["actual_orders"] = actual_orders
        fixture["actual_outcome"] = outcome
        fixture["eval_sets"] = []
        return validate_fixture(fixture)
