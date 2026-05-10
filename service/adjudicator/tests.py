from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

import pytest

from adjudicator import adjudicate, get_options


# === Builder DSL ===


def classical_phase_progression() -> Dict[str, Any]:
    return {
        "seasons": ["Spring", "Fall"],
        "transitions": [
            {"from": {"season": "Spring", "type": "Movement"},
             "to": {"season": "Spring", "type": "Retreat", "yearDelta": 0}},
            {"from": {"season": "Spring", "type": "Retreat"},
             "to": {"season": "Fall", "type": "Movement", "yearDelta": 0}},
            {"from": {"season": "Fall", "type": "Movement"},
             "to": {"season": "Fall", "type": "Retreat", "yearDelta": 0}},
            {"from": {"season": "Fall", "type": "Retreat"},
             "to": {"season": "Fall", "type": "Adjustment", "yearDelta": 0}},
            {"from": {"season": "Fall", "type": "Adjustment"},
             "to": {"season": "Spring", "type": "Movement", "yearDelta": 1}},
        ],
    }


def _stub_geometry() -> Dict[str, Any]:
    return {
        "path": "M 0 0 L 1 0 L 1 1 L 0 1 Z",
        "labels": [],
        "unitPosition": {"x": 0, "y": 0},
        "dislodgedUnitPosition": {"x": 0, "y": 0},
    }


def _province(
    province_id: str,
    name: str,
    type_: str,
    supply_center: bool,
    home_nation: Optional[str],
    adjacencies: List[Dict[str, str]],
) -> Dict[str, Any]:
    p: Dict[str, Any] = {
        "id": province_id,
        "name": name,
        "type": type_,
        "supplyCenter": supply_center,
        "adjacencies": adjacencies,
        **_stub_geometry(),
    }
    if home_nation is not None:
        p["homeNation"] = home_nation
    if supply_center:
        p["supplyCenterPosition"] = {"x": 0, "y": 0}
    return p


def _named_coast(coast_id: str, name: str, parent: str, adjacencies: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "id": coast_id,
        "name": name,
        "parentProvince": parent,
        "adjacencies": adjacencies,
        "path": "M 0 0 L 1 0 L 1 1 Z",
        "unitPosition": {"x": 0, "y": 0},
        "dislodgedUnitPosition": {"x": 0, "y": 0},
    }


def _build_adjacency_index(edges: List[tuple]) -> Dict[str, List[Dict[str, str]]]:
    index: Dict[str, List[Dict[str, str]]] = {}
    for a, b, pass_ in edges:
        index.setdefault(a, []).append({"to": b, "pass": pass_})
        index.setdefault(b, []).append({"to": a, "pass": pass_})
    return index


def classical_variant() -> Dict[str, Any]:
    edges = [
        ("vie", "boh", "army"),
        ("vie", "tri", "army"),
        ("vie", "tyr", "army"),
        ("tri", "tyr", "both"),
        ("tri", "ven", "both"),
        ("tri", "adr", "fleet"),
        ("tyr", "ven", "army"),
        ("tyr", "boh", "army"),
        ("ven", "adr", "fleet"),
        ("boh", "vie", "army"),
        ("ber", "kie", "both"),
        ("ber", "mun", "army"),
        ("ber", "bal", "fleet"),
        ("kie", "mun", "army"),
        ("kie", "bal", "fleet"),
        ("mun", "tyr", "army"),
        ("mun", "boh", "army"),
        ("stp", "fin", "army"),
        ("stp/nc", "bar", "fleet"),
        ("stp/sc", "fin", "fleet"),
        ("stp/sc", "bot", "fleet"),
        ("stp/nc", "nwy", "fleet"),
        ("fin", "swe", "both"),
        ("fin", "bot", "fleet"),
        ("nwy", "bar", "fleet"),
        ("nwy", "swe", "both"),
        ("nwy", "ska", "fleet"),
        ("swe", "ska", "fleet"),
        ("swe", "bal", "fleet"),
        ("swe", "bot", "fleet"),
        ("bal", "bot", "fleet"),
        ("bar", "nrg", "fleet"),
        ("nrg", "ska", "fleet"),
        ("adr", "ven", "fleet"),
    ]
    edges = list(dict.fromkeys((min(a, b), max(a, b), p) for a, b, p in edges))

    adjacency_index = _build_adjacency_index(edges)

    province_meta = [
        ("vie", "Vienna", "land", True, "austria"),
        ("bud", "Budapest", "land", True, "austria"),
        ("tri", "Trieste", "coastal", True, "austria"),
        ("ber", "Berlin", "coastal", True, "germany"),
        ("kie", "Kiel", "coastal", True, "germany"),
        ("mun", "Munich", "land", True, "germany"),
        ("stp", "St. Petersburg", "land", True, "russia"),
        ("mos", "Moscow", "land", True, "russia"),
        ("nwy", "Norway", "coastal", True, None),
        ("swe", "Sweden", "coastal", True, None),
        ("ven", "Venice", "coastal", True, "italy"),
        ("boh", "Bohemia", "land", False, None),
        ("tyr", "Tyrolia", "land", False, None),
        ("fin", "Finland", "coastal", False, None),
        ("adr", "Adriatic Sea", "sea", False, None),
        ("bal", "Baltic Sea", "sea", False, None),
        ("bar", "Barents Sea", "sea", False, None),
        ("bot", "Gulf of Bothnia", "sea", False, None),
        ("nrg", "Norwegian Sea", "sea", False, None),
        ("ska", "Skagerrak", "sea", False, None),
    ]

    provinces = [
        _province(pid, name, type_, sc, home, adjacency_index.get(pid, []))
        for pid, name, type_, sc, home in province_meta
    ]

    named_coasts = [
        _named_coast("stp/nc", "St. Petersburg (NC)", "stp", adjacency_index.get("stp/nc", [])),
        _named_coast("stp/sc", "St. Petersburg (SC)", "stp", adjacency_index.get("stp/sc", [])),
    ]

    return {
        "schemaVersion": 1,
        "id": "classical",
        "name": "Classical",
        "description": "The original game of Diplomacy.",
        "author": "Allan B. Calhamer",
        "soloVictorySupplyCenters": 18,
        "phaseProgression": classical_phase_progression(),
        "nations": [
            {"id": "austria", "name": "Austria", "color": "#F44336"},
            {"id": "germany", "name": "Germany", "color": "#90A4AE"},
            {"id": "italy", "name": "Italy", "color": "#4CAF50"},
            {"id": "russia", "name": "Russia", "color": "#F5F5F5"},
        ],
        "provinces": provinces,
        "namedCoasts": named_coasts,
        "initialState": {
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": [
                {"nation": "austria", "type": "Army", "location": "vie"},
                {"nation": "austria", "type": "Army", "location": "bud"},
                {"nation": "austria", "type": "Fleet", "location": "tri"},
                {"nation": "germany", "type": "Army", "location": "mun"},
                {"nation": "germany", "type": "Fleet", "location": "kie"},
                {"nation": "germany", "type": "Army", "location": "ber"},
                {"nation": "italy", "type": "Fleet", "location": "ven"},
                {"nation": "russia", "type": "Army", "location": "mos"},
                {"nation": "russia", "type": "Fleet", "location": "stp/sc"},
            ],
            "supplyCenters": [
                {"nation": "austria", "province": "vie"},
                {"nation": "austria", "province": "bud"},
                {"nation": "austria", "province": "tri"},
                {"nation": "germany", "province": "ber"},
                {"nation": "germany", "province": "kie"},
                {"nation": "germany", "province": "mun"},
                {"nation": "italy", "province": "ven"},
                {"nation": "russia", "province": "mos"},
                {"nation": "russia", "province": "stp"},
            ],
        },
        "dimensions": {"width": 1000, "height": 1000},
        "decorativeElements": [],
    }


def initial_game_state(variant: Dict[str, Any]) -> Dict[str, Any]:
    initial = variant["initialState"]
    return {
        "phase": dict(initial["phase"]),
        "units": [
            {**unit, "dislodged": False} for unit in initial["units"]
        ],
        "supplyCenters": [dict(sc) for sc in initial["supplyCenters"]],
        "orders": [],
        "resolutions": None,
        "skipped": False,
        "outcome": None,
    }


class StateBuilder:
    def __init__(self, variant: Dict[str, Any]):
        self.variant = variant
        self._state = initial_game_state(variant)
        self._state["units"] = []
        self._state["supplyCenters"] = []

    def at_phase(self, season: str, year: int, type_: str) -> "StateBuilder":
        self._state["phase"] = {"season": season, "year": year, "type": type_}
        return self

    def with_unit(self, nation: str, type_: str, location: str, *, dislodged: bool = False) -> "StateBuilder":
        self._state["units"].append(
            {"nation": nation, "type": type_, "location": location, "dislodged": dislodged}
        )
        return self

    def with_supply_center(self, nation: str, province: str) -> "StateBuilder":
        self._state["supplyCenters"].append({"nation": nation, "province": province})
        return self

    def with_order(
        self,
        nation: str,
        source: str,
        order_type: str,
        *,
        target: Optional[str] = None,
        aux: Optional[str] = None,
        unit_type: Optional[str] = None,
    ) -> "StateBuilder":
        self._state["orders"].append(
            {
                "nation": nation,
                "source": source,
                "orderType": order_type,
                "target": target,
                "aux": aux,
                "unitType": unit_type,
            }
        )
        return self

    def build(self) -> Dict[str, Any]:
        return copy.deepcopy(self._state)


def adjudicate_one(variant: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    result = adjudicate(variant, state)
    assert result, "adjudicate returned an empty list"
    return result[0]


def units_at(state: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    return [u for u in state["units"] if u["location"] == location]


def has_unit(state: Dict[str, Any], nation: str, type_: str, location: str) -> bool:
    return any(
        u["nation"] == nation and u["type"] == type_ and u["location"] == location
        for u in state["units"]
    )


def supply_center_owner(state: Dict[str, Any], province: str) -> Optional[str]:
    for sc in state["supplyCenters"]:
        if sc["province"] == province:
            return sc["nation"]
    return None


# === Phase 1 tests ===


def test_adjudicate_returns_initial_state_unchanged():
    variant = classical_variant()
    state = initial_game_state(variant)

    result = adjudicate(variant, state)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == state


def test_get_options_returns_empty_list():
    variant = classical_variant()
    state = initial_game_state(variant)

    options = get_options(variant, state)

    assert options == []


# === Loader sanity tests ===


def test_loader_rejects_unknown_phase_type_in_initial_state():
    variant = classical_variant()
    variant["initialState"]["phase"]["type"] = "Negotiation"

    with pytest.raises(Exception):
        adjudicate(variant, initial_game_state(variant))


def test_loader_rejects_unknown_unit_type_in_initial_state():
    variant = classical_variant()
    variant["initialState"]["units"][0] = {
        "nation": "austria",
        "type": "Spy",
        "location": "vie",
    }

    with pytest.raises(Exception):
        adjudicate(variant, initial_game_state(variant))


def test_loader_rejects_asymmetric_adjacency():
    variant = classical_variant()
    for province in variant["provinces"]:
        if province["id"] == "vie":
            province["adjacencies"].append({"to": "ber", "pass": "army"})
            break

    with pytest.raises(Exception):
        adjudicate(variant, initial_game_state(variant))


def test_loader_rejects_unknown_order_type_in_game_state():
    variant = classical_variant()
    state = initial_game_state(variant)
    state["orders"].append(
        {
            "nation": "austria",
            "source": "vie",
            "orderType": "Sabotage",
            "target": None,
            "aux": None,
            "unitType": None,
        }
    )

    with pytest.raises(Exception):
        adjudicate(variant, state)


def test_state_builder_round_trips_through_adjudicate():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "vie")
        .with_supply_center("austria", "vie")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "vie")
    assert supply_center_owner(result, "vie") == "austria"


def test_adjudicate_round_trips_state_with_orders_resolutions_and_outcome():
    variant = classical_variant()
    state = initial_game_state(variant)
    state["orders"] = [
        {
            "nation": "austria",
            "source": "vie",
            "orderType": "Hold",
            "target": None,
            "aux": None,
            "unitType": None,
        },
        {
            "nation": "germany",
            "source": "mun",
            "orderType": "Move",
            "target": "boh",
            "aux": None,
            "unitType": None,
        },
    ]
    state["resolutions"] = [
        {"province": "vie", "resolution": "OK"},
        {"province": "mun", "resolution": "OK"},
    ]
    state["outcome"] = {"winners": ["austria"], "reason": "solo", "year": 1908}

    result = adjudicate(variant, state)

    assert result == [state]
