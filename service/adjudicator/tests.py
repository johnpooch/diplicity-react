from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

import pytest

from adjudicator import adjudicate, get_options

# === Builder DSL ===


def classical_phase_progression() -> Dict[str, Any]:
    return {
        "seasons": ["Spring", "Fall"],
        "transitions": [
            {
                "from": {"season": "Spring", "type": "Movement"},
                "to": {"season": "Spring", "type": "Retreat", "yearDelta": 0},
            },
            {
                "from": {"season": "Spring", "type": "Retreat"},
                "to": {"season": "Fall", "type": "Movement", "yearDelta": 0},
            },
            {
                "from": {"season": "Fall", "type": "Movement"},
                "to": {"season": "Fall", "type": "Retreat", "yearDelta": 0},
            },
            {
                "from": {"season": "Fall", "type": "Retreat"},
                "to": {"season": "Fall", "type": "Adjustment", "yearDelta": 0},
            },
            {
                "from": {"season": "Fall", "type": "Adjustment"},
                "to": {"season": "Spring", "type": "Movement", "yearDelta": 1},
            },
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


def _named_coast(
    coast_id: str, name: str, parent: str, adjacencies: List[Dict[str, str]]
) -> Dict[str, Any]:
    return {
        "id": coast_id,
        "name": name,
        "parentProvince": parent,
        "adjacencies": adjacencies,
        "path": "M 0 0 L 1 0 L 1 1 Z",
        "unitPosition": {"x": 0, "y": 0},
        "dislodgedUnitPosition": {"x": 0, "y": 0},
    }


def _build_adjacency_index(
    edges: List[Tuple[str, str, str]],
) -> Dict[str, List[Dict[str, str]]]:
    index: Dict[str, List[Dict[str, str]]] = {}
    for a, b, pass_ in edges:
        index.setdefault(a, []).append({"to": b, "pass": pass_})
        index.setdefault(b, []).append({"to": a, "pass": pass_})
    return index


# Standard Classical Diplomacy provinces.
_PROVINCE_META: List[Tuple[str, str, str, bool, Optional[str]]] = [
    # Austria
    ("vie", "Vienna", "land", True, "austria"),
    ("bud", "Budapest", "land", True, "austria"),
    ("tri", "Trieste", "coastal", True, "austria"),
    # England
    ("lon", "London", "coastal", True, "england"),
    ("lvp", "Liverpool", "coastal", True, "england"),
    ("edi", "Edinburgh", "coastal", True, "england"),
    # France
    ("par", "Paris", "land", True, "france"),
    ("mar", "Marseilles", "coastal", True, "france"),
    ("bre", "Brest", "coastal", True, "france"),
    # Germany
    ("ber", "Berlin", "coastal", True, "germany"),
    ("kie", "Kiel", "coastal", True, "germany"),
    ("mun", "Munich", "land", True, "germany"),
    # Italy
    ("rom", "Rome", "coastal", True, "italy"),
    ("ven", "Venice", "coastal", True, "italy"),
    ("nap", "Naples", "coastal", True, "italy"),
    # Russia
    ("mos", "Moscow", "land", True, "russia"),
    ("stp", "St. Petersburg", "land", True, "russia"),
    ("sev", "Sevastopol", "coastal", True, "russia"),
    ("war", "Warsaw", "land", True, "russia"),
    # Turkey
    ("ank", "Ankara", "coastal", True, "turkey"),
    ("con", "Constantinople", "coastal", True, "turkey"),
    ("smy", "Smyrna", "coastal", True, "turkey"),
    # Neutral SC
    ("bel", "Belgium", "coastal", True, None),
    ("bul", "Bulgaria", "land", True, None),
    ("den", "Denmark", "coastal", True, None),
    ("gre", "Greece", "coastal", True, None),
    ("hol", "Holland", "coastal", True, None),
    ("nwy", "Norway", "coastal", True, None),
    ("por", "Portugal", "coastal", True, None),
    ("rum", "Rumania", "coastal", True, None),
    ("ser", "Serbia", "land", True, None),
    ("spa", "Spain", "land", True, None),
    ("swe", "Sweden", "coastal", True, None),
    ("tun", "Tunis", "coastal", True, None),
    # Non-SC land
    ("alb", "Albania", "coastal", False, None),
    ("apu", "Apulia", "coastal", False, None),
    ("arm", "Armenia", "coastal", False, None),
    ("boh", "Bohemia", "land", False, None),
    ("bur", "Burgundy", "land", False, None),
    ("cly", "Clyde", "coastal", False, None),
    ("fin", "Finland", "coastal", False, None),
    ("gal", "Galicia", "land", False, None),
    ("gas", "Gascony", "coastal", False, None),
    ("lvn", "Livonia", "coastal", False, None),
    ("naf", "North Africa", "coastal", False, None),
    ("pic", "Picardy", "coastal", False, None),
    ("pie", "Piedmont", "coastal", False, None),
    ("pru", "Prussia", "coastal", False, None),
    ("ruh", "Ruhr", "land", False, None),
    ("sil", "Silesia", "land", False, None),
    ("syr", "Syria", "coastal", False, None),
    ("tus", "Tuscany", "coastal", False, None),
    ("tyr", "Tyrolia", "land", False, None),
    ("ukr", "Ukraine", "land", False, None),
    ("wal", "Wales", "coastal", False, None),
    ("yor", "Yorkshire", "coastal", False, None),
    # Sea provinces
    ("adr", "Adriatic Sea", "sea", False, None),
    ("aeg", "Aegean Sea", "sea", False, None),
    ("bal", "Baltic Sea", "sea", False, None),
    ("bar", "Barents Sea", "sea", False, None),
    ("bla", "Black Sea", "sea", False, None),
    ("eas", "Eastern Mediterranean", "sea", False, None),
    ("eng", "English Channel", "sea", False, None),
    ("bot", "Gulf of Bothnia", "sea", False, None),
    ("lyo", "Gulf of Lyon", "sea", False, None),
    ("hel", "Helgoland Bight", "sea", False, None),
    ("ion", "Ionian Sea", "sea", False, None),
    ("iri", "Irish Sea", "sea", False, None),
    ("mao", "Mid-Atlantic Ocean", "sea", False, None),
    ("nao", "North Atlantic Ocean", "sea", False, None),
    ("nrg", "Norwegian Sea", "sea", False, None),
    ("nth", "North Sea", "sea", False, None),
    ("ska", "Skagerrak", "sea", False, None),
    ("tys", "Tyrrhenian Sea", "sea", False, None),
    ("wes", "Western Mediterranean", "sea", False, None),
]


# Standard Classical Diplomacy adjacencies. Each edge listed once; the loader mirrors.
_EDGES: List[Tuple[str, str, str]] = [
    # --- Sea-to-sea ---
    ("adr", "ion", "fleet"),
    ("aeg", "ion", "fleet"),
    ("aeg", "eas", "fleet"),
    ("bal", "bot", "fleet"),
    ("bar", "nrg", "fleet"),
    ("bar", "nwy", "fleet"),
    ("bla", "ank", "fleet"),
    ("eas", "ion", "fleet"),
    ("eng", "iri", "fleet"),
    ("eng", "mao", "fleet"),
    ("eng", "nth", "fleet"),
    ("hel", "nth", "fleet"),
    ("ion", "tys", "fleet"),
    ("iri", "mao", "fleet"),
    ("iri", "nao", "fleet"),
    ("lyo", "tys", "fleet"),
    ("lyo", "wes", "fleet"),
    ("mao", "nao", "fleet"),
    ("mao", "wes", "fleet"),
    ("nao", "nrg", "fleet"),
    ("nrg", "nth", "fleet"),
    ("nth", "ska", "fleet"),
    ("tys", "wes", "fleet"),
    # --- Sea-to-coastal (fleet) ---
    ("adr", "alb", "fleet"),
    ("adr", "apu", "fleet"),
    ("adr", "tri", "fleet"),
    ("adr", "ven", "fleet"),
    ("aeg", "con", "fleet"),
    ("aeg", "gre", "fleet"),
    ("aeg", "smy", "fleet"),
    ("bal", "ber", "fleet"),
    ("bal", "den", "fleet"),
    ("bal", "kie", "fleet"),
    ("bal", "lvn", "fleet"),
    ("bal", "pru", "fleet"),
    ("bal", "swe", "fleet"),
    ("bot", "fin", "fleet"),
    ("bot", "lvn", "fleet"),
    ("bot", "swe", "fleet"),
    ("bla", "arm", "fleet"),
    ("bla", "con", "fleet"),
    ("bla", "rum", "fleet"),
    ("bla", "sev", "fleet"),
    ("eas", "smy", "fleet"),
    ("eas", "syr", "fleet"),
    ("eng", "bel", "fleet"),
    ("eng", "bre", "fleet"),
    ("eng", "lon", "fleet"),
    ("eng", "pic", "fleet"),
    ("eng", "wal", "fleet"),
    ("hel", "den", "fleet"),
    ("hel", "hol", "fleet"),
    ("hel", "kie", "fleet"),
    ("ion", "alb", "fleet"),
    ("ion", "apu", "fleet"),
    ("ion", "gre", "fleet"),
    ("ion", "nap", "fleet"),
    ("ion", "tun", "fleet"),
    ("iri", "lvp", "fleet"),
    ("iri", "wal", "fleet"),
    ("lyo", "mar", "fleet"),
    ("lyo", "pie", "fleet"),
    ("lyo", "tus", "fleet"),
    ("mao", "bre", "fleet"),
    ("mao", "gas", "fleet"),
    ("mao", "naf", "fleet"),
    ("mao", "por", "fleet"),
    ("nao", "cly", "fleet"),
    ("nao", "lvp", "fleet"),
    ("nrg", "cly", "fleet"),
    ("nrg", "edi", "fleet"),
    ("nrg", "nwy", "fleet"),
    ("nth", "bel", "fleet"),
    ("nth", "den", "fleet"),
    ("nth", "edi", "fleet"),
    ("nth", "hol", "fleet"),
    ("nth", "lon", "fleet"),
    ("nth", "nwy", "fleet"),
    ("nth", "yor", "fleet"),
    ("ska", "den", "fleet"),
    ("ska", "nwy", "fleet"),
    ("ska", "swe", "fleet"),
    ("tys", "naf", "fleet"),
    ("tys", "nap", "fleet"),
    ("tys", "rom", "fleet"),
    ("tys", "tun", "fleet"),
    ("tys", "tus", "fleet"),
    ("wes", "naf", "fleet"),
    ("wes", "tun", "fleet"),
    # --- Coastal-coastal (both) ---
    ("alb", "gre", "both"),
    ("alb", "tri", "both"),
    ("ank", "con", "both"),
    ("ank", "smy", "both"),
    ("apu", "nap", "both"),
    ("apu", "ven", "both"),
    ("arm", "sev", "both"),
    ("arm", "smy", "both"),
    ("bel", "hol", "both"),
    ("bel", "pic", "both"),
    ("ber", "kie", "both"),
    ("ber", "pru", "both"),
    ("bre", "gas", "both"),
    ("bre", "pic", "both"),
    ("cly", "edi", "both"),
    ("cly", "lvp", "both"),
    ("con", "smy", "both"),
    ("den", "kie", "both"),
    ("den", "swe", "both"),
    ("edi", "yor", "both"),
    ("fin", "swe", "both"),
    ("gas", "mar", "both"),
    ("hol", "kie", "both"),
    ("kie", "hol", "both"),
    ("lon", "wal", "both"),
    ("lon", "yor", "both"),
    ("lvn", "pru", "both"),
    ("lvp", "wal", "both"),
    ("lvp", "yor", "both"),
    ("mar", "pie", "both"),
    ("naf", "tun", "both"),
    ("nap", "rom", "both"),
    ("nwy", "swe", "both"),
    ("pie", "tus", "both"),
    ("rom", "tus", "both"),
    ("rum", "sev", "both"),
    ("smy", "syr", "both"),
    ("tri", "ven", "both"),
    ("wal", "yor", "both"),
    # --- Coastal-coastal (army-only, no shared coast) ---
    ("apu", "rom", "army"),
    ("rom", "ven", "army"),
    ("edi", "lvp", "army"),
    ("ber", "mun", "army"),
    ("kie", "mun", "army"),
    ("kie", "ruh", "army"),
    ("hol", "ruh", "army"),
    ("bel", "ruh", "army"),
    ("bre", "par", "army"),
    ("gas", "par", "army"),
    ("gas", "spa", "army"),
    ("mar", "spa", "army"),
    ("por", "spa", "army"),
    # --- Land-to-land (army) ---
    ("boh", "vie", "army"),
    ("boh", "mun", "army"),
    ("boh", "sil", "army"),
    ("boh", "gal", "army"),
    ("boh", "tyr", "army"),
    ("bud", "vie", "army"),
    ("bud", "gal", "army"),
    ("bud", "rum", "army"),
    ("bud", "ser", "army"),
    ("bud", "tri", "army"),
    ("bur", "par", "army"),
    ("bur", "mar", "army"),
    ("bur", "gas", "army"),
    ("bur", "ruh", "army"),
    ("bur", "mun", "army"),
    ("bur", "bel", "army"),
    ("bur", "pic", "army"),
    ("gal", "vie", "army"),
    ("gal", "war", "army"),
    ("gal", "ukr", "army"),
    ("gal", "rum", "army"),
    ("gal", "sil", "army"),
    ("mos", "stp", "army"),
    ("mos", "lvn", "army"),
    ("mos", "war", "army"),
    ("mos", "ukr", "army"),
    ("mos", "sev", "army"),
    ("mun", "sil", "army"),
    ("mun", "tyr", "army"),
    ("mun", "ruh", "army"),
    ("par", "pic", "army"),
    ("ruh", "mun", "army"),
    ("ser", "rum", "army"),
    ("ser", "bul", "army"),
    ("ser", "gre", "army"),
    ("ser", "alb", "army"),
    ("ser", "tri", "army"),
    ("sil", "ber", "army"),
    ("sil", "war", "army"),
    ("sil", "pru", "army"),
    ("tyr", "vie", "army"),
    ("tyr", "ven", "army"),
    ("tyr", "tri", "army"),
    ("tyr", "pie", "army"),
    ("ukr", "war", "army"),
    ("ukr", "rum", "army"),
    ("ukr", "sev", "army"),
    ("war", "lvn", "army"),
    ("war", "pru", "army"),
    ("vie", "tri", "army"),
    # --- Coastal-land (army; coastal touches land) ---
    ("alb", "ser", "army"),
    ("ank", "arm", "army"),
    ("bel", "pic", "both"),  # already? duplicate ok (loader dedupes? Let's leave)
    ("bre", "pic", "both"),
    ("con", "bul", "army"),
    ("fin", "nwy", "army"),
    ("fin", "stp", "army"),
    ("gre", "bul", "army"),
    ("kie", "den", "both"),
    ("lvn", "stp", "army"),
    ("lvn", "mos", "army"),
    ("nwy", "stp", "army"),
    ("rum", "ukr", "army"),
    ("rum", "bul", "army"),
    ("rum", "gal", "army"),
    ("sev", "rum", "both"),
    ("smy", "syr", "both"),
    ("syr", "arm", "army"),
    ("tri", "vie", "army"),
    ("tri", "ven", "both"),
    # --- Multi-coast parent edges (armies use parent) ---
    # Bulgaria parent (army edges already covered: ser, gre, rum, con).
    # Spain parent (army edges already covered: por, mar, gas).
    # St. Petersburg parent (army edges already covered: fin, lvn, mos, nwy).
]


# Edges from named coasts. Mirrored on the parent's "to" via the schema convention:
# the parent province must NOT list these; only the named coast and the neighbour list them.
_NAMED_COAST_EDGES: List[Tuple[str, str, str]] = [
    # St Petersburg
    ("stp/nc", "bar", "fleet"),
    ("stp/nc", "nwy", "fleet"),
    ("stp/sc", "bot", "fleet"),
    ("stp/sc", "fin", "fleet"),
    # Spain
    ("spa/nc", "mao", "fleet"),
    ("spa/nc", "gas", "fleet"),
    ("spa/nc", "por", "fleet"),
    ("spa/sc", "mao", "fleet"),
    ("spa/sc", "wes", "fleet"),
    ("spa/sc", "lyo", "fleet"),
    ("spa/sc", "mar", "fleet"),
    ("spa/sc", "por", "fleet"),
    # Bulgaria
    ("bul/ec", "bla", "fleet"),
    ("bul/ec", "con", "fleet"),
    ("bul/ec", "rum", "fleet"),
    ("bul/sc", "aeg", "fleet"),
    ("bul/sc", "con", "fleet"),
    ("bul/sc", "gre", "fleet"),
]


def _dedupe_edges(edges: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    seen: Dict[Tuple[str, str, str], None] = {}
    for a, b, p in edges:
        key = (min(a, b), max(a, b), p)
        seen[key] = None
    return list(seen.keys())


def classical_variant() -> Dict[str, Any]:
    edges = _dedupe_edges(_EDGES)
    adjacency_index = _build_adjacency_index(edges)

    # Named-coast adjacencies are added as:
    #  - the named coast lists the neighbour in its own adjacencies
    #  - the neighbour lists the named coast id (not the parent) in its adjacencies
    for coast_id, neighbour, pass_ in _NAMED_COAST_EDGES:
        adjacency_index.setdefault(coast_id, []).append(
            {"to": neighbour, "pass": pass_}
        )
        adjacency_index.setdefault(neighbour, []).append(
            {"to": coast_id, "pass": pass_}
        )

    provinces = [
        _province(pid, name, type_, sc, home, adjacency_index.get(pid, []))
        for pid, name, type_, sc, home in _PROVINCE_META
    ]

    named_coasts = [
        _named_coast(
            "stp/nc", "St. Petersburg (NC)", "stp", adjacency_index.get("stp/nc", [])
        ),
        _named_coast(
            "stp/sc", "St. Petersburg (SC)", "stp", adjacency_index.get("stp/sc", [])
        ),
        _named_coast("spa/nc", "Spain (NC)", "spa", adjacency_index.get("spa/nc", [])),
        _named_coast("spa/sc", "Spain (SC)", "spa", adjacency_index.get("spa/sc", [])),
        _named_coast(
            "bul/ec", "Bulgaria (EC)", "bul", adjacency_index.get("bul/ec", [])
        ),
        _named_coast(
            "bul/sc", "Bulgaria (SC)", "bul", adjacency_index.get("bul/sc", [])
        ),
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
            {"id": "england", "name": "England", "color": "#1976D2"},
            {"id": "france", "name": "France", "color": "#80DEEA"},
            {"id": "germany", "name": "Germany", "color": "#90A4AE"},
            {"id": "italy", "name": "Italy", "color": "#4CAF50"},
            {"id": "russia", "name": "Russia", "color": "#F5F5F5"},
            {"id": "turkey", "name": "Turkey", "color": "#FFEB3B"},
        ],
        "provinces": provinces,
        "namedCoasts": named_coasts,
        "initialState": {
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": [
                {"nation": "austria", "type": "Army", "location": "vie"},
                {"nation": "austria", "type": "Army", "location": "bud"},
                {"nation": "austria", "type": "Fleet", "location": "tri"},
                {"nation": "england", "type": "Fleet", "location": "lon"},
                {"nation": "england", "type": "Fleet", "location": "edi"},
                {"nation": "england", "type": "Army", "location": "lvp"},
                {"nation": "france", "type": "Fleet", "location": "bre"},
                {"nation": "france", "type": "Army", "location": "par"},
                {"nation": "france", "type": "Army", "location": "mar"},
                {"nation": "germany", "type": "Army", "location": "mun"},
                {"nation": "germany", "type": "Fleet", "location": "kie"},
                {"nation": "germany", "type": "Army", "location": "ber"},
                {"nation": "italy", "type": "Fleet", "location": "nap"},
                {"nation": "italy", "type": "Army", "location": "ven"},
                {"nation": "italy", "type": "Army", "location": "rom"},
                {"nation": "russia", "type": "Army", "location": "mos"},
                {"nation": "russia", "type": "Fleet", "location": "stp/sc"},
                {"nation": "russia", "type": "Army", "location": "war"},
                {"nation": "russia", "type": "Fleet", "location": "sev"},
                {"nation": "turkey", "type": "Fleet", "location": "ank"},
                {"nation": "turkey", "type": "Army", "location": "con"},
                {"nation": "turkey", "type": "Army", "location": "smy"},
            ],
            "supplyCenters": [
                {"nation": "austria", "province": "vie"},
                {"nation": "austria", "province": "bud"},
                {"nation": "austria", "province": "tri"},
                {"nation": "england", "province": "lon"},
                {"nation": "england", "province": "lvp"},
                {"nation": "england", "province": "edi"},
                {"nation": "france", "province": "par"},
                {"nation": "france", "province": "mar"},
                {"nation": "france", "province": "bre"},
                {"nation": "germany", "province": "ber"},
                {"nation": "germany", "province": "kie"},
                {"nation": "germany", "province": "mun"},
                {"nation": "italy", "province": "ven"},
                {"nation": "italy", "province": "rom"},
                {"nation": "italy", "province": "nap"},
                {"nation": "russia", "province": "mos"},
                {"nation": "russia", "province": "stp"},
                {"nation": "russia", "province": "war"},
                {"nation": "russia", "province": "sev"},
                {"nation": "turkey", "province": "ank"},
                {"nation": "turkey", "province": "con"},
                {"nation": "turkey", "province": "smy"},
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
            {**unit, "dislodged": False, "dislodgedFrom": None}
            for unit in initial["units"]
        ],
        "supplyCenters": [dict(sc) for sc in initial["supplyCenters"]],
        "orders": [],
        "resolutions": None,
        "skipped": False,
        "outcome": None,
        "contestedProvinces": [],
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

    def with_unit(
        self,
        nation: str,
        type_: str,
        location: str,
        *,
        dislodged: bool = False,
        dislodged_from: Optional[str] = None,
    ) -> "StateBuilder":
        self._state["units"].append(
            {
                "nation": nation,
                "type": type_,
                "location": location,
                "dislodged": dislodged,
                "dislodgedFrom": dislodged_from,
            }
        )
        return self

    def with_contested(self, *provinces: str) -> "StateBuilder":
        self._state["contestedProvinces"] = list(provinces)
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
        via_convoy: bool = False,
    ) -> "StateBuilder":
        self._state["orders"].append(
            {
                "nation": nation,
                "source": source,
                "orderType": order_type,
                "target": target,
                "aux": aux,
                "unitType": unit_type,
                "viaConvoy": via_convoy,
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


def has_unit(
    state: Dict[str, Any],
    nation: str,
    type_: str,
    location: str,
    *,
    dislodged: bool = False,
) -> bool:
    return any(
        u["nation"] == nation
        and u["type"] == type_
        and u["location"] == location
        and u["dislodged"] == dislodged
        for u in state["units"]
    )


def supply_center_owner(state: Dict[str, Any], province: str) -> Optional[str]:
    for sc in state["supplyCenters"]:
        if sc["province"] == province:
            return sc["nation"]
    return None


def resolution_for(state: Dict[str, Any], province: str) -> Optional[str]:
    for r in state.get("resolutions") or []:
        if r["province"] == province:
            return r["resolution"]
    return None


def is_dislodged(state: Dict[str, Any], location: str) -> bool:
    return any(u["location"] == location and u["dislodged"] for u in state["units"])


# === Foundation tests ===


def test_adjudicate_with_no_orders_holds_all_units():
    variant = classical_variant()
    state = initial_game_state(variant)

    result = adjudicate(variant, state)

    assert isinstance(result, list)
    assert len(result) == 2
    resolved = result[0]
    assert resolved["phase"] == state["phase"]
    assert resolved["units"] == state["units"]
    assert resolved["supplyCenters"] == state["supplyCenters"]
    assert resolved["resolutions"] is not None
    assert all(r["resolution"] == "OK" for r in resolved["resolutions"])
    next_state = result[1]
    assert next_state["phase"] == {"season": "Spring", "year": 1901, "type": "Retreat"}
    assert next_state["resolutions"] is None
    assert next_state["units"] == state["units"]


def test_get_options_in_movement_phase_includes_hold_for_each_unit():
    variant = classical_variant()
    state = initial_game_state(variant)

    options = get_options(variant, state)

    unit_locations = {u["location"] for u in state["units"]}
    hold_sources = {o["source"] for o in options if o["orderType"] == "Hold"}

    assert hold_sources == unit_locations
    assert all(o["target"] is None for o in options if o["orderType"] == "Hold")


def test_get_options_includes_legal_move_targets_for_army():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "vie")
        .build()
    )

    options = get_options(variant, state)
    move_targets = {
        o["target"]
        for o in options
        if o["orderType"] == "Move" and o["source"] == "vie"
    }

    assert move_targets == {"boh", "tri", "tyr", "gal", "bud"}


def test_get_options_excludes_fleet_only_targets_for_army():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lvp")
        .build()
    )

    options = get_options(variant, state)
    move_targets = {
        o["target"]
        for o in options
        if o["orderType"] == "Move" and o["source"] == "lvp"
    }

    assert "iri" not in move_targets


def test_get_options_excludes_army_only_targets_for_fleet():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("italy", "Fleet", "rom")
        .build()
    )

    options = get_options(variant, state)
    move_targets = {
        o["target"]
        for o in options
        if o["orderType"] == "Move" and o["source"] == "rom"
    }

    assert "ven" not in move_targets
    assert "apu" not in move_targets
    assert "tus" in move_targets
    assert "tys" in move_targets


def test_get_options_outside_movement_phase_returns_empty_list():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("austria", "Army", "vie")
        .build()
    )

    assert get_options(variant, state) == []


def test_get_options_includes_support_for_adjacent_unit_move():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .build()
    )

    options = get_options(variant, state)
    support_options = [
        o for o in options if o["orderType"] == "Support" and o["source"] == "tyr"
    ]

    assert any(o["target"] == "ven" and o["aux"] == "ven" for o in support_options)


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
            province["adjacencies"].append({"to": "lon", "pass": "army"})
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


# === DATC 6.A: BASIC CHECKS ===


def test_a_1_moving_to_an_area_that_is_not_a_neighbour():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_order("england", "nth", "Move", target="pic")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "nth")
    assert not has_unit(result, "england", "Fleet", "pic")
    assert resolution_for(result, "nth") == "ILLEGAL"


def test_illegal_move_carries_failure_reason():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_order("england", "nth", "Move", target="pic")
        .build()
    )

    result = adjudicate_one(variant, state)

    nth_resolution = next(r for r in result["resolutions"] if r["province"] == "nth")
    assert nth_resolution["resolution"] == "ILLEGAL"
    assert nth_resolution["reason"] == "The unit can't reach the target province."


def test_a_2_move_army_to_sea():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lvp")
        .with_order("england", "lvp", "Move", target="iri")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "lvp")
    assert not units_at(result, "iri")
    assert resolution_for(result, "lvp") == "ILLEGAL"


def test_a_3_move_fleet_to_land():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Fleet", "kie")
        .with_order("germany", "kie", "Move", target="mun")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Fleet", "kie")
    assert not units_at(result, "mun")
    assert resolution_for(result, "kie") == "ILLEGAL"


def test_a_4_move_to_own_sector():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Fleet", "kie")
        .with_order("germany", "kie", "Move", target="kie")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Fleet", "kie")
    assert resolution_for(result, "kie") == "ILLEGAL"


def test_a_5_move_to_own_sector_with_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "yor")
        .with_unit("england", "Army", "lvp")
        .with_unit("germany", "Fleet", "lon")
        .with_unit("germany", "Fleet", "wal")
        .with_order("england", "nth", "Convoy", aux="yor", target="yor")
        .with_order("england", "yor", "Move", target="yor")
        .with_order("england", "lvp", "Support", aux="yor", target="yor")
        .with_order("germany", "lon", "Move", target="yor")
        .with_order("germany", "wal", "Support", aux="lon", target="yor")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "yor") == "ILLEGAL"
    # Liverpool's support is for a Yorkshire that ordered Move; the support
    # doesn't apply, regardless of how Yorkshire's order resolves.
    assert resolution_for(result, "lvp") != "OK"
    assert has_unit(result, "germany", "Fleet", "yor")
    assert is_dislodged(result, "yor")


def test_a_6_ordering_a_unit_of_another_country():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_order("germany", "lon", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "lon")
    assert not units_at(result, "nth")


def test_a_7_only_armies_can_be_convoyed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "nth")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "lon")
    assert has_unit(result, "england", "Fleet", "nth")
    assert not units_at(result, "bel")
    assert resolution_for(result, "lon") == "ILLEGAL"


def test_a_8_support_to_hold_yourself_is_not_possible():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .with_unit("austria", "Fleet", "tri")
        .with_order("italy", "ven", "Move", target="tri")
        .with_order("italy", "tyr", "Support", aux="ven", target="tri")
        .with_order("austria", "tri", "Support", aux="tri")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "tri") == "ILLEGAL"
    assert has_unit(result, "italy", "Army", "tri")
    assert is_dislodged(result, "tri")


def test_a_9_fleets_must_follow_coast_if_not_on_sea():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("italy", "Fleet", "rom")
        .with_order("italy", "rom", "Move", target="ven")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Fleet", "rom")
    assert resolution_for(result, "rom") == "ILLEGAL"


def test_a_10_support_on_unreachable_destination_not_possible():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "ven")
        .with_unit("italy", "Fleet", "rom")
        .with_unit("italy", "Army", "apu")
        .with_order("austria", "ven", "Hold")
        .with_order("italy", "rom", "Support", aux="apu", target="ven")
        .with_order("italy", "apu", "Move", target="ven")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "ven")
    assert has_unit(result, "italy", "Army", "apu")
    assert has_unit(result, "italy", "Fleet", "rom")
    assert resolution_for(result, "apu") == "BOUNCE"


def test_a_11_simple_bounce():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "vie")
        .with_unit("italy", "Army", "ven")
        .with_order("austria", "vie", "Move", target="tyr")
        .with_order("italy", "ven", "Move", target="tyr")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "vie")
    assert has_unit(result, "italy", "Army", "ven")
    assert units_at(result, "tyr") == []
    assert resolution_for(result, "vie") == "BOUNCE"
    assert resolution_for(result, "ven") == "BOUNCE"


def test_a_12_bounce_of_three_units():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "vie")
        .with_unit("germany", "Army", "mun")
        .with_unit("italy", "Army", "ven")
        .with_order("austria", "vie", "Move", target="tyr")
        .with_order("germany", "mun", "Move", target="tyr")
        .with_order("italy", "ven", "Move", target="tyr")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "vie")
    assert has_unit(result, "germany", "Army", "mun")
    assert has_unit(result, "italy", "Army", "ven")
    assert units_at(result, "tyr") == []
    assert resolution_for(result, "vie") == "BOUNCE"
    assert resolution_for(result, "mun") == "BOUNCE"
    assert resolution_for(result, "ven") == "BOUNCE"


# === DATC 6.C: CIRCULAR MOVEMENT ===


def test_c_1_three_army_circular_movement():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("turkey", "Fleet", "ank")
        .with_unit("turkey", "Army", "con")
        .with_unit("turkey", "Army", "smy")
        .with_order("turkey", "ank", "Move", target="con")
        .with_order("turkey", "con", "Move", target="smy")
        .with_order("turkey", "smy", "Move", target="ank")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Fleet", "con")
    assert has_unit(result, "turkey", "Army", "smy")
    assert has_unit(result, "turkey", "Army", "ank")
    assert resolution_for(result, "ank") == "OK"
    assert resolution_for(result, "con") == "OK"
    assert resolution_for(result, "smy") == "OK"


def test_c_2_three_army_circular_movement_with_support():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("turkey", "Fleet", "ank")
        .with_unit("turkey", "Army", "smy")
        .with_unit("turkey", "Army", "bul")
        .with_unit("italy", "Army", "con")
        .with_order("turkey", "ank", "Move", target="con")
        .with_order("turkey", "smy", "Move", target="ank")
        .with_order("turkey", "bul", "Support", aux="ank", target="con")
        .with_order("italy", "con", "Move", target="smy")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Fleet", "con")
    assert has_unit(result, "turkey", "Army", "ank")
    assert has_unit(result, "italy", "Army", "smy")
    assert resolution_for(result, "ank") == "OK"
    assert resolution_for(result, "con") == "OK"
    assert resolution_for(result, "smy") == "OK"


def test_c_3_disrupted_three_army_circular_movement():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("turkey", "Fleet", "ank")
        .with_unit("turkey", "Army", "con")
        .with_unit("turkey", "Army", "smy")
        .with_unit("turkey", "Army", "bul")
        .with_order("turkey", "ank", "Move", target="con")
        .with_order("turkey", "con", "Move", target="smy")
        .with_order("turkey", "smy", "Move", target="ank")
        .with_order("turkey", "bul", "Move", target="con")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Fleet", "ank")
    assert has_unit(result, "turkey", "Army", "con")
    assert has_unit(result, "turkey", "Army", "smy")
    assert has_unit(result, "turkey", "Army", "bul")


def test_c_4_circular_movement_with_attacked_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "tri")
        .with_unit("austria", "Army", "ser")
        .with_unit("turkey", "Army", "bul")
        .with_unit("turkey", "Fleet", "aeg")
        .with_unit("turkey", "Fleet", "ion")
        .with_unit("turkey", "Fleet", "adr")
        .with_unit("italy", "Fleet", "nap")
        .with_order("austria", "tri", "Move", target="ser")
        .with_order("austria", "ser", "Move", target="bul")
        .with_order("turkey", "bul", "Move", target="tri")
        .with_order("turkey", "aeg", "Convoy", aux="bul", target="tri")
        .with_order("turkey", "ion", "Convoy", aux="bul", target="tri")
        .with_order("turkey", "adr", "Convoy", aux="bul", target="tri")
        .with_order("italy", "nap", "Move", target="ion")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "ser")
    assert has_unit(result, "austria", "Army", "bul")
    assert has_unit(result, "turkey", "Army", "tri")
    assert has_unit(result, "italy", "Fleet", "nap")
    assert has_unit(result, "turkey", "Fleet", "ion")


def test_c_5_disrupted_circular_movement_due_to_dislodged_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "tri")
        .with_unit("austria", "Army", "ser")
        .with_unit("turkey", "Army", "bul")
        .with_unit("turkey", "Fleet", "aeg")
        .with_unit("turkey", "Fleet", "ion")
        .with_unit("turkey", "Fleet", "adr")
        .with_unit("italy", "Fleet", "nap")
        .with_unit("italy", "Fleet", "tun")
        .with_order("austria", "tri", "Move", target="ser")
        .with_order("austria", "ser", "Move", target="bul")
        .with_order("turkey", "bul", "Move", target="tri")
        .with_order("turkey", "aeg", "Convoy", aux="bul", target="tri")
        .with_order("turkey", "ion", "Convoy", aux="bul", target="tri")
        .with_order("turkey", "adr", "Convoy", aux="bul", target="tri")
        .with_order("italy", "nap", "Move", target="ion")
        .with_order("italy", "tun", "Support", aux="nap", target="ion")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "tri")
    assert has_unit(result, "austria", "Army", "ser")
    assert has_unit(result, "turkey", "Army", "bul")
    assert is_dislodged(result, "ion")
    assert has_unit(result, "italy", "Fleet", "ion")


def test_c_6_two_armies_with_two_convoys():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Army", "bel")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("france", "eng", "Convoy", aux="bel", target="lon")
        .with_order("france", "bel", "Move", target="lon")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bel")
    assert has_unit(result, "france", "Army", "lon")


def test_c_7_disrupted_unit_swap():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Army", "bel")
        .with_unit("france", "Army", "bur")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("france", "eng", "Convoy", aux="bel", target="lon")
        .with_order("france", "bel", "Move", target="lon")
        .with_order("france", "bur", "Move", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "lon")
    assert has_unit(result, "france", "Army", "bel")
    assert has_unit(result, "france", "Army", "bur")


# === DATC 6.D: SUPPORTS AND DISLODGES ===


def test_d_1_supported_hold_can_prevent_dislodgment():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "adr")
        .with_unit("austria", "Army", "tri")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .with_order("austria", "adr", "Support", aux="tri", target="ven")
        .with_order("austria", "tri", "Move", target="ven")
        .with_order("italy", "ven", "Hold")
        .with_order("italy", "tyr", "Support", aux="ven")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Army", "ven")
    assert has_unit(result, "austria", "Army", "tri")
    assert resolution_for(result, "tri") == "BOUNCE"


def test_d_2_move_cuts_support_on_hold():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "adr")
        .with_unit("austria", "Army", "tri")
        .with_unit("austria", "Army", "vie")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .with_order("austria", "adr", "Support", aux="tri", target="ven")
        .with_order("austria", "tri", "Move", target="ven")
        .with_order("austria", "vie", "Move", target="tyr")
        .with_order("italy", "ven", "Hold")
        .with_order("italy", "tyr", "Support", aux="ven")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "ven")
    assert is_dislodged(result, "ven")
    assert resolution_for(result, "tyr") == "CUT"


def test_d_3_move_cuts_support_on_move():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "adr")
        .with_unit("austria", "Army", "tri")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Fleet", "ion")
        .with_order("austria", "adr", "Support", aux="tri", target="ven")
        .with_order("austria", "tri", "Move", target="ven")
        .with_order("italy", "ven", "Hold")
        .with_order("italy", "ion", "Move", target="adr")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Army", "ven")
    assert resolution_for(result, "tri") == "BOUNCE"
    assert resolution_for(result, "adr") == "CUT"


def test_d_4_support_to_hold_on_unit_supporting_hold_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("russia", "Fleet", "bal")
        .with_unit("russia", "Army", "pru")
        .with_order("germany", "ber", "Support", aux="kie")
        .with_order("germany", "kie", "Support", aux="ber")
        .with_order("russia", "bal", "Support", aux="pru", target="ber")
        .with_order("russia", "pru", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert resolution_for(result, "pru") == "BOUNCE"
    assert resolution_for(result, "ber") == "CUT"
    assert resolution_for(result, "kie") == "OK"


def test_d_5_support_to_hold_on_unit_supporting_move_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("germany", "Army", "mun")
        .with_unit("russia", "Fleet", "bal")
        .with_unit("russia", "Army", "pru")
        .with_order("germany", "ber", "Support", aux="mun", target="sil")
        .with_order("germany", "kie", "Support", aux="ber")
        .with_order("germany", "mun", "Move", target="sil")
        .with_order("russia", "bal", "Support", aux="pru", target="ber")
        .with_order("russia", "pru", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "sil")
    assert has_unit(result, "germany", "Army", "ber")
    assert resolution_for(result, "pru") == "BOUNCE"
    assert resolution_for(result, "ber") == "CUT"


def test_d_6_support_to_hold_on_convoying_unit_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "bal")
        .with_unit("germany", "Fleet", "pru")
        .with_unit("russia", "Fleet", "lvn")
        .with_unit("russia", "Fleet", "bot")
        .with_order("germany", "ber", "Move", target="swe")
        .with_order("germany", "bal", "Convoy", aux="ber", target="swe")
        .with_order("germany", "pru", "Support", aux="bal")
        .with_order("russia", "lvn", "Move", target="bal")
        .with_order("russia", "bot", "Support", aux="lvn", target="bal")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "swe")
    assert has_unit(result, "germany", "Fleet", "bal")
    assert resolution_for(result, "lvn") == "BOUNCE"


def test_d_7_support_to_hold_on_moving_unit_not_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Fleet", "bal")
        .with_unit("germany", "Fleet", "pru")
        .with_unit("russia", "Fleet", "lvn")
        .with_unit("russia", "Fleet", "bot")
        .with_unit("russia", "Army", "fin")
        .with_order("germany", "bal", "Move", target="swe")
        .with_order("germany", "pru", "Support", aux="bal")
        .with_order("russia", "lvn", "Move", target="bal")
        .with_order("russia", "bot", "Support", aux="lvn", target="bal")
        .with_order("russia", "fin", "Move", target="swe")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "russia", "Fleet", "bal")
    assert is_dislodged(result, "bal")
    assert resolution_for(result, "bal") == "BOUNCE"
    assert resolution_for(result, "pru") == "CUT"


def test_d_8_failed_convoy_cannot_receive_hold_support():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "ion")
        .with_unit("austria", "Army", "ser")
        .with_unit("austria", "Army", "alb")
        .with_unit("turkey", "Army", "gre")
        .with_unit("turkey", "Army", "bul")
        .with_order("austria", "ion", "Hold")
        .with_order("austria", "ser", "Support", aux="alb", target="gre")
        .with_order("austria", "alb", "Move", target="gre")
        .with_order("turkey", "gre", "Move", target="nap")
        .with_order("turkey", "bul", "Support", aux="gre")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "gre")
    assert is_dislodged(result, "gre")
    assert resolution_for(result, "bul") == "CUT"
    assert resolution_for(result, "gre") == "BOUNCE"


def test_d_9_support_to_move_on_holding_unit_not_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .with_unit("austria", "Army", "alb")
        .with_unit("austria", "Army", "tri")
        .with_order("italy", "ven", "Move", target="tri")
        .with_order("italy", "tyr", "Support", aux="ven", target="tri")
        .with_order("austria", "alb", "Support", aux="tri", target="ser")
        .with_order("austria", "tri", "Hold")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Army", "tri")
    assert is_dislodged(result, "tri")
    assert resolution_for(result, "alb") == "CUT"


def test_d_10_self_dislodgment_prohibited():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("germany", "Army", "mun")
        .with_order("germany", "ber", "Hold")
        .with_order("germany", "kie", "Move", target="ber")
        .with_order("germany", "mun", "Support", aux="kie", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert has_unit(result, "germany", "Fleet", "kie")
    assert resolution_for(result, "kie") == "BOUNCE"


def test_d_11_no_self_dislodgment_of_returning_unit():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("germany", "Army", "mun")
        .with_unit("russia", "Army", "war")
        .with_order("germany", "ber", "Move", target="pru")
        .with_order("germany", "kie", "Move", target="ber")
        .with_order("germany", "mun", "Support", aux="kie", target="ber")
        .with_order("russia", "war", "Move", target="pru")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert has_unit(result, "germany", "Fleet", "kie")
    assert has_unit(result, "russia", "Army", "war")
    assert resolution_for(result, "ber") == "BOUNCE"
    assert resolution_for(result, "kie") == "BOUNCE"
    assert resolution_for(result, "war") == "BOUNCE"


def test_d_12_supporting_foreign_unit_to_dislodge_own_unit_prohibited():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "tri")
        .with_unit("austria", "Army", "vie")
        .with_unit("italy", "Army", "ven")
        .with_order("austria", "tri", "Hold")
        .with_order("austria", "vie", "Support", aux="ven", target="tri")
        .with_order("italy", "ven", "Move", target="tri")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Fleet", "tri")
    assert has_unit(result, "italy", "Army", "ven")
    assert resolution_for(result, "ven") == "BOUNCE"


def test_d_14_supporting_foreign_unit_is_not_enough_to_prevent_dislodgment():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "tri")
        .with_unit("austria", "Army", "vie")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .with_unit("italy", "Fleet", "adr")
        .with_order("austria", "tri", "Hold")
        .with_order("austria", "vie", "Support", aux="ven", target="tri")
        .with_order("italy", "ven", "Move", target="tri")
        .with_order("italy", "tyr", "Support", aux="ven", target="tri")
        .with_order("italy", "adr", "Support", aux="ven", target="tri")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Army", "tri")
    assert is_dislodged(result, "tri")


def test_d_15_defender_cannot_cut_support_for_attack_on_itself():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("russia", "Fleet", "con")
        .with_unit("russia", "Fleet", "bla")
        .with_unit("turkey", "Fleet", "ank")
        .with_order("russia", "con", "Support", aux="bla", target="ank")
        .with_order("russia", "bla", "Move", target="ank")
        .with_order("turkey", "ank", "Move", target="con")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "russia", "Fleet", "ank")
    assert is_dislodged(result, "ank")
    assert resolution_for(result, "con") == "OK"


def test_d_17_dislodgment_cuts_supports():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("russia", "Fleet", "con")
        .with_unit("russia", "Fleet", "bla")
        .with_unit("turkey", "Fleet", "ank")
        .with_unit("turkey", "Army", "smy")
        .with_unit("turkey", "Army", "arm")
        .with_order("russia", "con", "Support", aux="bla", target="ank")
        .with_order("russia", "bla", "Move", target="ank")
        .with_order("turkey", "ank", "Move", target="con")
        .with_order("turkey", "smy", "Support", aux="ank", target="con")
        .with_order("turkey", "arm", "Move", target="ank")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Fleet", "con")
    assert is_dislodged(result, "con")
    assert resolution_for(result, "bla") == "BOUNCE"
    assert resolution_for(result, "arm") == "BOUNCE"


def test_d_18_surviving_unit_will_sustain_support():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("russia", "Fleet", "con")
        .with_unit("russia", "Fleet", "bla")
        .with_unit("russia", "Army", "bul")
        .with_unit("turkey", "Fleet", "ank")
        .with_unit("turkey", "Army", "smy")
        .with_unit("turkey", "Army", "arm")
        .with_order("russia", "con", "Support", aux="bla", target="ank")
        .with_order("russia", "bla", "Move", target="ank")
        .with_order("russia", "bul", "Support", aux="con")
        .with_order("turkey", "ank", "Move", target="con")
        .with_order("turkey", "smy", "Support", aux="ank", target="con")
        .with_order("turkey", "arm", "Move", target="ank")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "russia", "Fleet", "ank")
    assert is_dislodged(result, "ank")
    assert resolution_for(result, "ank") == "BOUNCE"


def test_d_20_unit_cannot_cut_support_of_its_own_country():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "yor")
        .with_unit("france", "Fleet", "eng")
        .with_order("england", "lon", "Support", aux="nth", target="eng")
        .with_order("england", "nth", "Move", target="eng")
        .with_order("england", "yor", "Move", target="lon")
        .with_order("france", "eng", "Hold")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "eng")
    assert is_dislodged(result, "eng")
    assert resolution_for(result, "lon") == "OK"
    assert resolution_for(result, "yor") == "BOUNCE"


def test_d_21_dislodging_does_not_cancel_a_support_cut():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "tri")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Army", "tyr")
        .with_unit("germany", "Army", "mun")
        .with_unit("russia", "Army", "sil")
        .with_unit("russia", "Army", "ber")
        .with_order("austria", "tri", "Hold")
        .with_order("italy", "ven", "Move", target="tri")
        .with_order("italy", "tyr", "Support", aux="ven", target="tri")
        .with_order("germany", "mun", "Move", target="tyr")
        .with_order("russia", "sil", "Move", target="mun")
        .with_order("russia", "ber", "Support", aux="sil", target="mun")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Fleet", "tri")
    assert has_unit(result, "russia", "Army", "mun")
    assert is_dislodged(result, "mun")
    assert resolution_for(result, "ven") == "BOUNCE"
    assert resolution_for(result, "tyr") == "CUT"


def test_d_22_impossible_fleet_move_cannot_be_supported():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("germany", "Army", "bur")
        .with_unit("russia", "Army", "mun")
        .with_unit("russia", "Army", "ber")
        .with_order("germany", "kie", "Move", target="mun")
        .with_order("germany", "bur", "Support", aux="kie", target="mun")
        .with_order("russia", "mun", "Move", target="kie")
        .with_order("russia", "ber", "Support", aux="mun", target="kie")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "kie") == "ILLEGAL"
    assert resolution_for(result, "bur") == "ILLEGAL"
    assert has_unit(result, "russia", "Army", "kie")


def test_d_24_impossible_army_move_cannot_be_supported():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Army", "mar")
        .with_unit("france", "Fleet", "spa/sc")
        .with_unit("italy", "Fleet", "lyo")
        .with_unit("turkey", "Fleet", "tys")
        .with_unit("turkey", "Fleet", "wes")
        .with_order("france", "mar", "Move", target="lyo")
        .with_order("france", "spa/sc", "Support", aux="mar", target="lyo")
        .with_order("italy", "lyo", "Hold")
        .with_order("turkey", "tys", "Support", aux="wes", target="lyo")
        .with_order("turkey", "wes", "Move", target="lyo")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "mar") == "ILLEGAL"
    assert resolution_for(result, "spa/sc") == "ILLEGAL"
    assert has_unit(result, "turkey", "Fleet", "lyo")
    assert is_dislodged(result, "lyo")


def test_d_25_invalid_hold_support_can_be_supported():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("russia", "Fleet", "bal")
        .with_unit("russia", "Army", "pru")
        .with_order("germany", "ber", "Support", aux="pru")
        .with_order("germany", "kie", "Support", aux="ber")
        .with_order("russia", "bal", "Support", aux="pru", target="ber")
        .with_order("russia", "pru", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert resolution_for(result, "pru") == "BOUNCE"


def test_d_26_invalid_move_support_can_be_supported():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("russia", "Fleet", "bal")
        .with_unit("russia", "Army", "pru")
        .with_order("germany", "ber", "Support", aux="pru", target="sil")
        .with_order("germany", "kie", "Support", aux="ber")
        .with_order("russia", "bal", "Support", aux="pru", target="ber")
        .with_order("russia", "pru", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert resolution_for(result, "pru") == "BOUNCE"


def test_d_28_impossible_move_and_support():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "bud")
        .with_unit("russia", "Fleet", "rum")
        .with_unit("turkey", "Fleet", "bla")
        .with_unit("turkey", "Army", "bul")
        .with_order("austria", "bud", "Support", aux="rum")
        .with_order("russia", "rum", "Move", target="hol")
        .with_order("turkey", "bla", "Move", target="rum")
        .with_order("turkey", "bul", "Support", aux="bla", target="rum")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "russia", "Fleet", "rum")
    assert resolution_for(result, "rum") == "ILLEGAL"
    assert resolution_for(result, "bla") == "BOUNCE"


def test_d_33_unwanted_support_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "ser")
        .with_unit("austria", "Army", "vie")
        .with_unit("russia", "Army", "gal")
        .with_unit("turkey", "Army", "bul")
        .with_order("austria", "ser", "Move", target="bud")
        .with_order("austria", "vie", "Move", target="bud")
        .with_order("russia", "gal", "Support", aux="ser", target="bud")
        .with_order("turkey", "bul", "Move", target="ser")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "bud")
    assert has_unit(result, "turkey", "Army", "ser")
    assert resolution_for(result, "vie") == "BOUNCE"


def test_d_34_support_targeting_own_province_not_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Army", "sil")
        .with_unit("germany", "Fleet", "bal")
        .with_unit("italy", "Army", "pru")
        .with_unit("russia", "Army", "war")
        .with_unit("russia", "Army", "lvn")
        .with_order("germany", "ber", "Move", target="pru")
        .with_order("germany", "sil", "Support", aux="ber", target="pru")
        .with_order("germany", "bal", "Support", aux="ber", target="pru")
        .with_order("italy", "pru", "Support", aux="lvn", target="pru")
        .with_order("russia", "war", "Support", aux="lvn", target="pru")
        .with_order("russia", "lvn", "Move", target="pru")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "pru")
    assert is_dislodged(result, "pru")
    assert resolution_for(result, "pru") == "ILLEGAL"


def test_d_35_dislodgment_cuts_supports_allowing_enemy_to_advance():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("russia", "Fleet", "bla")
        .with_unit("russia", "Fleet", "con")
        .with_unit("turkey", "Fleet", "ank")
        .with_unit("turkey", "Fleet", "aeg")
        .with_unit("turkey", "Army", "arm")
        .with_unit("turkey", "Army", "smy")
        .with_order("russia", "bla", "Move", target="ank")
        .with_order("russia", "con", "Support", aux="bla", target="ank")
        .with_order("turkey", "ank", "Move", target="con")
        .with_order("turkey", "aeg", "Support", aux="ank", target="con")
        .with_order("turkey", "arm", "Move", target="ank")
        .with_order("turkey", "smy", "Support", aux="arm", target="ank")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Fleet", "con")
    assert is_dislodged(result, "con")
    assert has_unit(result, "turkey", "Army", "ank")
    assert resolution_for(result, "bla") == "BOUNCE"
    assert resolution_for(result, "ank") == "OK"
    assert resolution_for(result, "arm") == "OK"


# === DATC 6.E: HEAD-TO-HEAD AND BELEAGUERED GARRISON ===


def test_e_1_dislodged_unit_has_no_effect_on_attackers_province():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("germany", "Army", "sil")
        .with_unit("russia", "Army", "pru")
        .with_order("germany", "ber", "Move", target="pru")
        .with_order("germany", "kie", "Move", target="ber")
        .with_order("germany", "sil", "Support", aux="ber", target="pru")
        .with_order("russia", "pru", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "pru")
    assert has_unit(result, "germany", "Fleet", "ber")
    assert is_dislodged(result, "pru")


def test_e_2_no_self_dislodgment_in_head_to_head_battle():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "kie")
        .with_unit("germany", "Army", "mun")
        .with_order("germany", "ber", "Move", target="kie")
        .with_order("germany", "kie", "Move", target="ber")
        .with_order("germany", "mun", "Support", aux="ber", target="kie")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert has_unit(result, "germany", "Fleet", "kie")
    assert resolution_for(result, "ber") == "BOUNCE"
    assert resolution_for(result, "kie") == "BOUNCE"


def test_e_3_no_help_in_dislodging_own_unit():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Army", "mun")
        .with_unit("england", "Fleet", "kie")
        .with_order("germany", "ber", "Move", target="kie")
        .with_order("germany", "mun", "Support", aux="kie", target="ber")
        .with_order("england", "kie", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "ber")
    assert has_unit(result, "england", "Fleet", "kie")


def test_e_6_not_dislodge_because_of_own_support_still_has_effect():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Fleet", "hol")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("france", "Fleet", "nth")
        .with_unit("france", "Fleet", "bel")
        .with_unit("france", "Fleet", "eng")
        .with_unit("austria", "Army", "kie")
        .with_unit("austria", "Army", "ruh")
        .with_order("germany", "hol", "Move", target="nth")
        .with_order("germany", "hel", "Support", aux="hol", target="nth")
        .with_order("france", "nth", "Move", target="hol")
        .with_order("france", "bel", "Support", aux="nth", target="hol")
        .with_order("france", "eng", "Support", aux="hol", target="nth")
        .with_order("austria", "kie", "Support", aux="ruh", target="hol")
        .with_order("austria", "ruh", "Move", target="hol")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Fleet", "hol")
    assert has_unit(result, "france", "Fleet", "nth")
    assert has_unit(result, "austria", "Army", "ruh")
    assert resolution_for(result, "hol") == "BOUNCE"
    assert resolution_for(result, "nth") == "BOUNCE"
    assert resolution_for(result, "ruh") == "BOUNCE"


def test_e_7_no_self_dislodgment_with_beleaguered_garrison():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Fleet", "yor")
        .with_unit("germany", "Fleet", "hol")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("russia", "Fleet", "ska")
        .with_unit("russia", "Fleet", "nwy")
        .with_order("england", "nth", "Hold")
        .with_order("england", "yor", "Support", aux="nwy", target="nth")
        .with_order("germany", "hol", "Support", aux="hel", target="nth")
        .with_order("germany", "hel", "Move", target="nth")
        .with_order("russia", "ska", "Support", aux="nwy", target="nth")
        .with_order("russia", "nwy", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "nth")
    assert has_unit(result, "russia", "Fleet", "nwy")
    assert has_unit(result, "germany", "Fleet", "hel")
    assert resolution_for(result, "nwy") == "BOUNCE"
    assert resolution_for(result, "hel") == "BOUNCE"


def test_e_8_no_self_dislodgment_with_beleaguered_garrison_and_head_to_head():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Fleet", "yor")
        .with_unit("germany", "Fleet", "hol")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("russia", "Fleet", "ska")
        .with_unit("russia", "Fleet", "nwy")
        .with_order("england", "nth", "Move", target="nwy")
        .with_order("england", "yor", "Support", aux="nwy", target="nth")
        .with_order("germany", "hol", "Support", aux="hel", target="nth")
        .with_order("germany", "hel", "Move", target="nth")
        .with_order("russia", "ska", "Support", aux="nwy", target="nth")
        .with_order("russia", "nwy", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "nth")
    assert has_unit(result, "russia", "Fleet", "nwy")
    assert has_unit(result, "germany", "Fleet", "hel")
    assert resolution_for(result, "nth") == "BOUNCE"
    assert resolution_for(result, "nwy") == "BOUNCE"
    assert resolution_for(result, "hel") == "BOUNCE"


def test_e_9_almost_self_dislodgment_with_beleaguered_garrison():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Fleet", "yor")
        .with_unit("germany", "Fleet", "hol")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("russia", "Fleet", "ska")
        .with_unit("russia", "Fleet", "nwy")
        .with_order("england", "nth", "Move", target="nrg")
        .with_order("england", "yor", "Support", aux="nwy", target="nth")
        .with_order("germany", "hol", "Support", aux="hel", target="nth")
        .with_order("germany", "hel", "Move", target="nth")
        .with_order("russia", "ska", "Support", aux="nwy", target="nth")
        .with_order("russia", "nwy", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "nrg")
    assert has_unit(result, "russia", "Fleet", "nth")
    assert has_unit(result, "germany", "Fleet", "hel")
    assert resolution_for(result, "nth") == "OK"
    assert resolution_for(result, "nwy") == "OK"
    assert resolution_for(result, "hel") == "BOUNCE"


def test_e_12_support_on_attack_on_own_unit_can_be_used_for_other_means():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Army", "bud")
        .with_unit("austria", "Army", "ser")
        .with_unit("italy", "Army", "vie")
        .with_unit("russia", "Army", "gal")
        .with_unit("russia", "Army", "rum")
        .with_order("austria", "bud", "Move", target="rum")
        .with_order("austria", "ser", "Support", aux="vie", target="bud")
        .with_order("italy", "vie", "Move", target="bud")
        .with_order("russia", "gal", "Move", target="bud")
        .with_order("russia", "rum", "Support", aux="gal", target="bud")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "austria", "Army", "bud")
    assert resolution_for(result, "vie") == "BOUNCE"
    assert resolution_for(result, "gal") == "BOUNCE"


def test_e_13_three_way_beleaguered_garrison():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "edi")
        .with_unit("england", "Fleet", "yor")
        .with_unit("france", "Fleet", "bel")
        .with_unit("france", "Fleet", "eng")
        .with_unit("germany", "Fleet", "nth")
        .with_unit("russia", "Fleet", "nrg")
        .with_unit("russia", "Fleet", "nwy")
        .with_order("england", "edi", "Support", aux="yor", target="nth")
        .with_order("england", "yor", "Move", target="nth")
        .with_order("france", "bel", "Move", target="nth")
        .with_order("france", "eng", "Support", aux="bel", target="nth")
        .with_order("germany", "nth", "Hold")
        .with_order("russia", "nrg", "Move", target="nth")
        .with_order("russia", "nwy", "Support", aux="nrg", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Fleet", "nth")
    assert resolution_for(result, "yor") == "BOUNCE"
    assert resolution_for(result, "bel") == "BOUNCE"
    assert resolution_for(result, "nrg") == "BOUNCE"


def test_e_14_illegal_head_to_head_battle_can_still_defend():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lvp")
        .with_unit("russia", "Fleet", "edi")
        .with_order("england", "lvp", "Move", target="edi")
        .with_order("russia", "edi", "Move", target="lvp")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "lvp")
    assert has_unit(result, "russia", "Fleet", "edi")
    assert resolution_for(result, "lvp") == "BOUNCE"
    assert resolution_for(result, "edi") == "ILLEGAL"


def test_e_15_friendly_head_to_head_battle():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "hol")
        .with_unit("england", "Army", "ruh")
        .with_unit("france", "Army", "kie")
        .with_unit("france", "Army", "mun")
        .with_unit("france", "Army", "sil")
        .with_unit("germany", "Army", "ber")
        .with_unit("germany", "Fleet", "den")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("russia", "Fleet", "bal")
        .with_unit("russia", "Army", "pru")
        .with_order("england", "hol", "Support", aux="ruh", target="kie")
        .with_order("england", "ruh", "Move", target="kie")
        .with_order("france", "kie", "Move", target="ber")
        .with_order("france", "mun", "Support", aux="kie", target="ber")
        .with_order("france", "sil", "Support", aux="kie", target="ber")
        .with_order("germany", "ber", "Move", target="kie")
        .with_order("germany", "den", "Support", aux="ber", target="kie")
        .with_order("germany", "hel", "Support", aux="ber", target="kie")
        .with_order("russia", "bal", "Support", aux="pru", target="ber")
        .with_order("russia", "pru", "Move", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Army", "kie")
    assert has_unit(result, "germany", "Army", "ber")
    assert resolution_for(result, "kie") == "BOUNCE"
    assert resolution_for(result, "ber") == "BOUNCE"
    assert resolution_for(result, "ruh") == "BOUNCE"
    assert resolution_for(result, "pru") == "BOUNCE"


# === DATC 6.F: CONVOYS ===


def test_f_1_no_convoy_in_coastal_areas():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("turkey", "Army", "gre")
        .with_unit("turkey", "Fleet", "aeg")
        .with_unit("turkey", "Fleet", "con")
        .with_unit("turkey", "Fleet", "bla")
        .with_order("turkey", "gre", "Move", target="sev")
        .with_order("turkey", "aeg", "Convoy", aux="gre", target="sev")
        .with_order("turkey", "con", "Convoy", aux="gre", target="sev")
        .with_order("turkey", "bla", "Convoy", aux="gre", target="sev")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Army", "gre")


def test_f_2_an_army_being_convoyed_can_bounce_as_normal():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "eng")
        .with_unit("england", "Army", "lon")
        .with_unit("france", "Army", "par")
        .with_order("england", "eng", "Convoy", aux="lon", target="bre")
        .with_order("england", "lon", "Move", target="bre")
        .with_order("france", "par", "Move", target="bre")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "lon")
    assert has_unit(result, "france", "Army", "par")
    assert resolution_for(result, "lon") == "BOUNCE"
    assert resolution_for(result, "par") == "BOUNCE"


def test_f_3_an_army_being_convoyed_can_receive_support():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "eng")
        .with_unit("england", "Army", "lon")
        .with_unit("england", "Fleet", "mao")
        .with_unit("france", "Army", "par")
        .with_order("england", "eng", "Convoy", aux="lon", target="bre")
        .with_order("england", "lon", "Move", target="bre")
        .with_order("england", "mao", "Support", aux="lon", target="bre")
        .with_order("france", "par", "Move", target="bre")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bre")
    assert has_unit(result, "france", "Army", "par")


def test_f_4_an_attacked_convoy_is_not_disrupted():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("germany", "Fleet", "ska")
        .with_order("england", "nth", "Convoy", aux="lon", target="hol")
        .with_order("england", "lon", "Move", target="hol")
        .with_order("germany", "ska", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "hol")
    assert has_unit(result, "england", "Fleet", "nth")
    assert resolution_for(result, "ska") == "BOUNCE"


def test_f_5_a_beleaguered_convoy_is_not_disrupted():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Fleet", "bel")
        .with_unit("germany", "Fleet", "ska")
        .with_unit("germany", "Fleet", "den")
        .with_order("england", "nth", "Convoy", aux="lon", target="hol")
        .with_order("england", "lon", "Move", target="hol")
        .with_order("france", "eng", "Move", target="nth")
        .with_order("france", "bel", "Support", aux="eng", target="nth")
        .with_order("germany", "ska", "Move", target="nth")
        .with_order("germany", "den", "Support", aux="ska", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "hol")
    assert has_unit(result, "england", "Fleet", "nth")


def test_f_6_dislodged_convoy_does_not_cut_support():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("germany", "Army", "hol")
        .with_unit("germany", "Army", "bel")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("germany", "Fleet", "ska")
        .with_unit("france", "Army", "pic")
        .with_unit("france", "Army", "bur")
        .with_order("england", "nth", "Convoy", aux="lon", target="hol")
        .with_order("england", "lon", "Move", target="hol")
        .with_order("germany", "hol", "Support", aux="bel")
        .with_order("germany", "bel", "Support", aux="hol")
        .with_order("germany", "hel", "Support", aux="ska", target="nth")
        .with_order("germany", "ska", "Move", target="nth")
        .with_order("france", "pic", "Move", target="bel")
        .with_order("france", "bur", "Support", aux="pic", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Fleet", "nth")
    assert is_dislodged(result, "nth")
    assert has_unit(result, "germany", "Army", "bel")
    assert resolution_for(result, "pic") == "BOUNCE"


def test_f_7_dislodged_convoy_does_not_cause_contested_area():
    # The retreat-phase consequence is covered in Phase 5; here we just
    # verify the dislodgement happens and the convoy fails.
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("germany", "Fleet", "ska")
        .with_order("england", "nth", "Convoy", aux="lon", target="hol")
        .with_order("england", "lon", "Move", target="hol")
        .with_order("germany", "hel", "Support", aux="ska", target="nth")
        .with_order("germany", "ska", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert is_dislodged(result, "nth")
    assert has_unit(result, "england", "Army", "lon")
    assert resolution_for(result, "lon") == "BOUNCE"


def test_f_8_dislodged_convoy_does_not_cause_a_bounce():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("germany", "Fleet", "ska")
        .with_unit("germany", "Army", "bel")
        .with_order("england", "nth", "Convoy", aux="lon", target="hol")
        .with_order("england", "lon", "Move", target="hol")
        .with_order("germany", "hel", "Support", aux="ska", target="nth")
        .with_order("germany", "ska", "Move", target="nth")
        .with_order("germany", "bel", "Move", target="hol")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Army", "hol")
    assert resolution_for(result, "bel") == "OK"


def test_f_9_dislodge_of_multi_route_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "eng")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("france", "Fleet", "bre")
        .with_unit("france", "Fleet", "mao")
        .with_order("england", "eng", "Convoy", aux="lon", target="bel")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("france", "bre", "Support", aux="mao", target="eng")
        .with_order("france", "mao", "Move", target="eng")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bel")
    assert is_dislodged(result, "eng")
    assert has_unit(result, "france", "Fleet", "eng")


def test_f_10_dislodge_of_multi_route_convoy_with_foreign_fleet():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("germany", "Fleet", "eng")
        .with_unit("france", "Fleet", "bre")
        .with_unit("france", "Fleet", "mao")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("germany", "eng", "Convoy", aux="lon", target="bel")
        .with_order("france", "bre", "Support", aux="mao", target="eng")
        .with_order("france", "mao", "Move", target="eng")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bel")
    assert is_dislodged(result, "eng")
    assert has_unit(result, "france", "Fleet", "eng")


def test_f_11_dislodge_of_multi_route_convoy_with_only_foreign_fleets():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lon")
        .with_unit("germany", "Fleet", "eng")
        .with_unit("russia", "Fleet", "nth")
        .with_unit("france", "Fleet", "bre")
        .with_unit("france", "Fleet", "mao")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("germany", "eng", "Convoy", aux="lon", target="bel")
        .with_order("russia", "nth", "Convoy", aux="lon", target="bel")
        .with_order("france", "bre", "Support", aux="mao", target="eng")
        .with_order("france", "mao", "Move", target="eng")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bel")
    assert is_dislodged(result, "eng")
    assert has_unit(result, "france", "Fleet", "eng")


def test_f_12_dislodged_convoying_fleet_not_on_route():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "eng")
        .with_unit("england", "Army", "lon")
        .with_unit("england", "Fleet", "iri")
        .with_unit("france", "Fleet", "nao")
        .with_unit("france", "Fleet", "mao")
        .with_order("england", "eng", "Convoy", aux="lon", target="bel")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("england", "iri", "Convoy", aux="lon", target="bel")
        .with_order("france", "nao", "Support", aux="mao", target="iri")
        .with_order("france", "mao", "Move", target="iri")
        .build()
    )

    result = adjudicate_one(variant, state)

    # F IRI's convoy order is not on any minimal chain — it should be
    # declared illegal at parse time. The remaining convoy via ENG works
    # and IRI is dislodged by the French.
    assert has_unit(result, "england", "Army", "bel")
    assert is_dislodged(result, "iri")
    assert has_unit(result, "france", "Fleet", "iri")
    assert resolution_for(result, "iri") == "ILLEGAL"


def test_f_13_the_unwanted_alternative():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lon")
        .with_unit("england", "Fleet", "nth")
        .with_unit("france", "Fleet", "eng")
        .with_unit("germany", "Fleet", "hol")
        .with_unit("germany", "Fleet", "den")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("france", "eng", "Convoy", aux="lon", target="bel")
        .with_order("germany", "hol", "Support", aux="den", target="nth")
        .with_order("germany", "den", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bel")
    assert is_dislodged(result, "nth")
    assert has_unit(result, "germany", "Fleet", "nth")


def test_f_14_simple_convoy_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "wal")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_order("england", "lon", "Support", aux="wal", target="eng")
        .with_order("england", "wal", "Move", target="eng")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "eng")
    assert is_dislodged(result, "eng")
    assert resolution_for(result, "lon") == "OK"
    assert resolution_for(result, "bre") == "BOUNCE"


def test_f_15_simple_convoy_paradox_with_additional_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "wal")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_unit("italy", "Fleet", "iri")
        .with_unit("italy", "Fleet", "mao")
        .with_unit("italy", "Army", "naf")
        .with_order("england", "lon", "Support", aux="wal", target="eng")
        .with_order("england", "wal", "Move", target="eng")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .with_order("italy", "iri", "Convoy", aux="naf", target="wal")
        .with_order("italy", "mao", "Convoy", aux="naf", target="wal")
        .with_order("italy", "naf", "Move", target="wal")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Fleet", "eng")
    assert is_dislodged(result, "eng")
    assert has_unit(result, "italy", "Army", "wal")


def test_f_16_pandins_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "wal")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_unit("germany", "Fleet", "nth")
        .with_unit("germany", "Fleet", "bel")
        .with_order("england", "lon", "Support", aux="wal", target="eng")
        .with_order("england", "wal", "Move", target="eng")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .with_order("germany", "nth", "Support", aux="bel", target="eng")
        .with_order("germany", "bel", "Move", target="eng")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "eng")
    assert not is_dislodged(result, "eng")
    assert resolution_for(result, "wal") == "BOUNCE"
    assert resolution_for(result, "bel") == "BOUNCE"
    assert resolution_for(result, "bre") == "BOUNCE"


def test_f_17_pandins_extended_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "wal")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Fleet", "yor")
        .with_unit("germany", "Fleet", "nth")
        .with_unit("germany", "Fleet", "bel")
        .with_order("england", "lon", "Support", aux="wal", target="eng")
        .with_order("england", "wal", "Move", target="eng")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .with_order("france", "yor", "Support", aux="bre", target="lon")
        .with_order("germany", "nth", "Support", aux="bel", target="eng")
        .with_order("germany", "bel", "Move", target="eng")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: convoy fails, neither London nor English Channel is dislodged.
    assert has_unit(result, "england", "Fleet", "lon")
    assert not is_dislodged(result, "lon")
    assert has_unit(result, "france", "Fleet", "eng")
    assert not is_dislodged(result, "eng")


def test_f_18_betrayal_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "lon")
        .with_unit("england", "Fleet", "eng")
        .with_unit("france", "Fleet", "bel")
        .with_unit("germany", "Fleet", "hel")
        .with_unit("germany", "Fleet", "ska")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "lon", "Move", target="bel")
        .with_order("england", "eng", "Support", aux="lon", target="bel")
        .with_order("france", "bel", "Support", aux="nth")
        .with_order("germany", "hel", "Support", aux="ska", target="nth")
        .with_order("germany", "ska", "Move", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: convoy fails, North Sea is not dislodged.
    assert has_unit(result, "england", "Fleet", "nth")
    assert not is_dislodged(result, "nth")
    assert has_unit(result, "france", "Fleet", "bel")


def test_f_19_multi_route_convoy_disruption_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Army", "tun")
        .with_unit("france", "Fleet", "tys")
        .with_unit("france", "Fleet", "ion")
        .with_unit("italy", "Fleet", "nap")
        .with_unit("italy", "Fleet", "rom")
        .with_order("france", "tun", "Move", target="nap")
        .with_order("france", "tys", "Convoy", aux="tun", target="nap")
        .with_order("france", "ion", "Convoy", aux="tun", target="nap")
        .with_order("italy", "nap", "Support", aux="rom", target="tys")
        .with_order("italy", "rom", "Move", target="tys")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: support of Naples is cut; Tyrrhenian Sea is not dislodged.
    assert has_unit(result, "france", "Fleet", "tys")
    assert not is_dislodged(result, "tys")
    assert resolution_for(result, "rom") == "BOUNCE"


def test_f_20_unwanted_multi_route_convoy_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Army", "tun")
        .with_unit("france", "Fleet", "tys")
        .with_unit("italy", "Fleet", "nap")
        .with_unit("italy", "Fleet", "ion")
        .with_unit("turkey", "Fleet", "aeg")
        .with_unit("turkey", "Fleet", "eas")
        .with_order("france", "tun", "Move", target="nap")
        .with_order("france", "tys", "Convoy", aux="tun", target="nap")
        .with_order("italy", "nap", "Support", aux="ion")
        .with_order("italy", "ion", "Convoy", aux="tun", target="nap")
        .with_order("turkey", "aeg", "Support", aux="eas", target="ion")
        .with_order("turkey", "eas", "Move", target="ion")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: Naples support is cut, Ionian dislodged by Eastern Med.
    assert is_dislodged(result, "ion")
    assert has_unit(result, "turkey", "Fleet", "ion")


def test_f_21_dads_army_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("russia", "Army", "edi")
        .with_unit("russia", "Fleet", "nrg")
        .with_unit("russia", "Army", "nwy")
        .with_unit("france", "Fleet", "iri")
        .with_unit("france", "Fleet", "mao")
        .with_unit("england", "Army", "lvp")
        .with_unit("england", "Fleet", "nao")
        .with_unit("england", "Fleet", "cly")
        .with_order("russia", "edi", "Support", aux="nwy", target="cly")
        .with_order("russia", "nrg", "Convoy", aux="nwy", target="cly")
        .with_order("russia", "nwy", "Move", target="cly")
        .with_order("france", "iri", "Support", aux="mao", target="nao")
        .with_order("france", "mao", "Move", target="nao")
        .with_order("england", "lvp", "Move", target="cly", via_convoy=True)
        .with_order("england", "nao", "Convoy", aux="lvp", target="cly")
        .with_order("england", "cly", "Support", aux="nao")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: support of Clyde is cut, NAO dislodged.
    assert is_dislodged(result, "nao")
    assert has_unit(result, "france", "Fleet", "nao")


def test_f_22_second_order_paradox_with_two_resolutions():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "edi")
        .with_unit("england", "Fleet", "lon")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_unit("germany", "Fleet", "bel")
        .with_unit("germany", "Fleet", "pic")
        .with_unit("russia", "Army", "nwy")
        .with_unit("russia", "Fleet", "nth")
        .with_order("england", "edi", "Move", target="nth")
        .with_order("england", "lon", "Support", aux="edi", target="nth")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .with_order("germany", "bel", "Support", aux="pic", target="eng")
        .with_order("germany", "pic", "Move", target="eng")
        .with_order("russia", "nwy", "Move", target="bel")
        .with_order("russia", "nth", "Convoy", aux="nwy", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: convoying armies fail, supports stand, both convoying fleets
    # are dislodged.
    assert is_dislodged(result, "eng")
    assert is_dislodged(result, "nth")
    assert resolution_for(result, "bre") == "BOUNCE"
    assert resolution_for(result, "nwy") == "BOUNCE"


def test_f_23_second_order_paradox_with_two_exclusive_convoys():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "edi")
        .with_unit("england", "Fleet", "yor")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_unit("germany", "Fleet", "bel")
        .with_unit("germany", "Fleet", "lon")
        .with_unit("italy", "Fleet", "mao")
        .with_unit("italy", "Fleet", "iri")
        .with_unit("russia", "Army", "nwy")
        .with_unit("russia", "Fleet", "nth")
        .with_order("england", "edi", "Move", target="nth")
        .with_order("england", "yor", "Support", aux="edi", target="nth")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .with_order("germany", "bel", "Support", aux="eng")
        .with_order("germany", "lon", "Support", aux="nth")
        .with_order("italy", "mao", "Move", target="eng")
        .with_order("italy", "iri", "Support", aux="mao", target="eng")
        .with_order("russia", "nwy", "Move", target="bel")
        .with_order("russia", "nth", "Convoy", aux="nwy", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: convoying armies fail, supports stand, no fleet moves.
    assert resolution_for(result, "bre") == "BOUNCE"
    assert resolution_for(result, "nwy") == "BOUNCE"
    assert resolution_for(result, "edi") == "BOUNCE"
    assert resolution_for(result, "mao") == "BOUNCE"


def test_f_24_second_order_paradox_with_no_resolution():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "edi")
        .with_unit("england", "Fleet", "lon")
        .with_unit("england", "Fleet", "iri")
        .with_unit("england", "Fleet", "mao")
        .with_unit("france", "Army", "bre")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Fleet", "bel")
        .with_unit("russia", "Army", "nwy")
        .with_unit("russia", "Fleet", "nth")
        .with_order("england", "edi", "Move", target="nth")
        .with_order("england", "lon", "Support", aux="edi", target="nth")
        .with_order("england", "iri", "Move", target="eng")
        .with_order("england", "mao", "Support", aux="iri", target="eng")
        .with_order("france", "bre", "Move", target="lon")
        .with_order("france", "eng", "Convoy", aux="bre", target="lon")
        .with_order("france", "bel", "Support", aux="eng")
        .with_order("russia", "nwy", "Move", target="bel")
        .with_order("russia", "nth", "Convoy", aux="nwy", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: convoying armies fail, supports stand, NTH is dislodged but
    # ENG survives (BEL's support holds it).
    assert resolution_for(result, "bre") == "BOUNCE"
    assert resolution_for(result, "nwy") == "BOUNCE"
    assert is_dislodged(result, "nth")
    assert not is_dislodged(result, "eng")


def test_f_25_cut_support_last():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("germany", "Army", "ruh")
        .with_unit("germany", "Army", "hol")
        .with_unit("germany", "Army", "den")
        .with_unit("germany", "Fleet", "ska")
        .with_unit("germany", "Army", "fin")
        .with_unit("england", "Army", "yor")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Fleet", "hel")
        .with_unit("england", "Army", "bel")
        .with_unit("russia", "Fleet", "nrg")
        .with_unit("russia", "Fleet", "nwy")
        .with_unit("russia", "Fleet", "swe")
        .with_order("germany", "ruh", "Move", target="bel")
        .with_order("germany", "hol", "Support", aux="ruh", target="bel")
        .with_order("germany", "den", "Move", target="nwy")
        .with_order("germany", "ska", "Convoy", aux="den", target="nwy")
        .with_order("germany", "fin", "Support", aux="den", target="nwy")
        .with_order("england", "yor", "Move", target="hol", via_convoy=True)
        .with_order("england", "nth", "Convoy", aux="yor", target="hol")
        .with_order("england", "hel", "Support", aux="yor", target="hol")
        .with_order("england", "bel", "Hold")
        .with_order("russia", "nrg", "Move", target="nth")
        .with_order("russia", "nwy", "Support", aux="nrg", target="nth")
        .with_order("russia", "swe", "Move", target="ska")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Yorkshire's convoy succeeds, cutting Holland's support. Belgium is
    # not dislodged. Denmark moves to Norway (Sweden fails to disrupt
    # convoy). Norway's support is cut.
    assert has_unit(result, "england", "Army", "hol")
    assert has_unit(result, "england", "Army", "bel")
    assert has_unit(result, "germany", "Army", "nwy")


# === DATC 6.G: CONVOYING TO ADJACENT PROVINCES ===


def test_g_1_two_units_can_swap_provinces_by_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("england", "Fleet", "ska")
        .with_unit("russia", "Army", "swe")
        .with_order("england", "nwy", "Move", target="swe")
        .with_order("england", "ska", "Convoy", aux="nwy", target="swe")
        .with_order("russia", "swe", "Move", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "swe")
    assert has_unit(result, "russia", "Army", "nwy")


def test_g_2_kidnapping_an_army():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("russia", "Fleet", "swe")
        .with_unit("germany", "Fleet", "ska")
        .with_order("england", "nwy", "Move", target="swe")
        .with_order("russia", "swe", "Move", target="nwy")
        .with_order("germany", "ska", "Convoy", aux="nwy", target="swe")
        .build()
    )

    result = adjudicate_one(variant, state)

    # 2023 rules: foreign convoy provides no kidnap intent; armies fail.
    assert has_unit(result, "england", "Army", "nwy")
    assert has_unit(result, "russia", "Fleet", "swe")


def test_g_3_unwanted_disrupted_convoy_to_adjacent_province():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "bre")
        .with_unit("france", "Army", "pic")
        .with_unit("france", "Army", "bur")
        .with_unit("france", "Fleet", "mao")
        .with_unit("england", "Fleet", "eng")
        .with_order("france", "bre", "Move", target="eng")
        .with_order("france", "pic", "Move", target="bel")
        .with_order("france", "bur", "Support", aux="pic", target="bel")
        .with_order("france", "mao", "Support", aux="bre", target="eng")
        .with_order("england", "eng", "Convoy", aux="pic", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    # The army in Picardy takes the land route to Belgium; the convoy is
    # disrupted but unwanted.
    assert has_unit(result, "france", "Army", "bel")
    assert is_dislodged(result, "eng")


def test_g_4_unwanted_disrupted_convoy_to_adjacent_province_and_opposite_move():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "bre")
        .with_unit("france", "Army", "pic")
        .with_unit("france", "Army", "bur")
        .with_unit("france", "Fleet", "mao")
        .with_unit("england", "Fleet", "eng")
        .with_unit("england", "Army", "bel")
        .with_order("france", "bre", "Move", target="eng")
        .with_order("france", "pic", "Move", target="bel")
        .with_order("france", "bur", "Support", aux="pic", target="bel")
        .with_order("france", "mao", "Support", aux="bre", target="eng")
        .with_order("england", "eng", "Convoy", aux="pic", target="bel")
        .with_order("england", "bel", "Move", target="pic")
        .build()
    )

    result = adjudicate_one(variant, state)

    # 2023 rules: kidnapping prevented; Picardy takes land route to Belgium.
    assert has_unit(result, "france", "Army", "bel")
    assert is_dislodged(result, "bel")


def test_g_5_swapping_with_multiple_fleets_with_one_own_fleet():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("italy", "Army", "rom")
        .with_unit("italy", "Fleet", "tys")
        .with_unit("turkey", "Army", "apu")
        .with_unit("turkey", "Fleet", "ion")
        .with_order("italy", "rom", "Move", target="apu")
        .with_order("italy", "tys", "Convoy", aux="apu", target="rom")
        .with_order("turkey", "apu", "Move", target="rom")
        .with_order("turkey", "ion", "Convoy", aux="apu", target="rom")
        .build()
    )

    result = adjudicate_one(variant, state)

    # One own-nation fleet (Turkish ION) suffices to express intent.
    assert has_unit(result, "italy", "Army", "apu")
    assert has_unit(result, "turkey", "Army", "rom")


def test_g_6_swapping_with_unintended_intent():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lvp")
        .with_unit("england", "Fleet", "eng")
        .with_unit("germany", "Army", "edi")
        .with_unit("france", "Fleet", "iri")
        .with_unit("france", "Fleet", "nth")
        .with_unit("russia", "Fleet", "nrg")
        .with_unit("russia", "Fleet", "nao")
        .with_order("england", "lvp", "Move", target="edi")
        .with_order("england", "eng", "Convoy", aux="lvp", target="edi")
        .with_order("germany", "edi", "Move", target="lvp")
        .with_order("france", "iri", "Hold")
        .with_order("france", "nth", "Hold")
        .with_order("russia", "nrg", "Convoy", aux="lvp", target="edi")
        .with_order("russia", "nao", "Convoy", aux="lvp", target="edi")
        .build()
    )

    result = adjudicate_one(variant, state)

    # 2023 rules: England's own convoy intent triggers convoy; swap succeeds.
    assert has_unit(result, "england", "Army", "edi")
    assert has_unit(result, "germany", "Army", "lvp")


def test_g_7_swapping_with_illegal_intent():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "ska")
        .with_unit("england", "Fleet", "nwy")
        .with_unit("russia", "Army", "swe")
        .with_unit("russia", "Fleet", "bot")
        .with_order("england", "ska", "Convoy", aux="swe", target="nwy")
        .with_order("england", "nwy", "Move", target="swe")
        .with_order("russia", "swe", "Move", target="nwy")
        .with_order("russia", "bot", "Convoy", aux="swe", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # F BOT convoy is impossible (not on any chain); ignored. Without
    # own-nation convoy intent, the Russian move is direct, head-to-head
    # with the English fleet; both bounce.
    assert has_unit(result, "england", "Fleet", "nwy")
    assert has_unit(result, "russia", "Army", "swe")


def test_g_8_explicit_convoy_that_isnt_there():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Army", "bel")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "hol")
        .with_order("france", "bel", "Move", target="hol", via_convoy=True)
        .with_order("england", "nth", "Move", target="hel")
        .with_order("england", "hol", "Move", target="kie")
        .build()
    )

    result = adjudicate_one(variant, state)

    # 2023: no fallback to land route; Belgium's convoy fails.
    assert has_unit(result, "france", "Army", "bel")
    assert has_unit(result, "england", "Fleet", "hel")
    assert has_unit(result, "england", "Army", "kie")


def test_g_9_swapped_or_dislodged():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("england", "Fleet", "ska")
        .with_unit("england", "Fleet", "fin")
        .with_unit("russia", "Army", "swe")
        .with_order("england", "nwy", "Move", target="swe")
        .with_order("england", "ska", "Convoy", aux="nwy", target="swe")
        .with_order("england", "fin", "Support", aux="nwy", target="swe")
        .with_order("russia", "swe", "Move", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # 2023: convoy is used; armies swap.
    assert has_unit(result, "england", "Army", "swe")
    assert has_unit(result, "russia", "Army", "nwy")


def test_g_10_swapped_or_an_head_to_head_battle():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("england", "Fleet", "den")
        .with_unit("england", "Fleet", "fin")
        .with_unit("germany", "Fleet", "ska")
        .with_unit("russia", "Army", "swe")
        .with_unit("russia", "Fleet", "bar")
        .with_unit("france", "Fleet", "nrg")
        .with_unit("france", "Fleet", "nth")
        .with_order("england", "nwy", "Move", target="swe", via_convoy=True)
        .with_order("england", "den", "Support", aux="nwy", target="swe")
        .with_order("england", "fin", "Support", aux="nwy", target="swe")
        .with_order("germany", "ska", "Convoy", aux="nwy", target="swe")
        .with_order("russia", "swe", "Move", target="nwy")
        .with_order("russia", "bar", "Support", aux="swe", target="nwy")
        .with_order("france", "nrg", "Move", target="nwy")
        .with_order("france", "nth", "Support", aux="nrg", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # NOR-SWE is via convoy (explicit), so it's not head-to-head with SWE-NOR.
    # NOR dislodges SWE. SWE-NOR and NRG-NOR mutually bounce.
    assert has_unit(result, "england", "Army", "swe")
    assert is_dislodged(result, "swe")
    assert resolution_for(result, "swe") == "BOUNCE"
    assert resolution_for(result, "nrg") == "BOUNCE"


def test_g_11_convoy_to_adjacent_province_with_paradox():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nwy")
        .with_unit("england", "Fleet", "nth")
        .with_unit("russia", "Army", "swe")
        .with_unit("russia", "Fleet", "ska")
        .with_unit("russia", "Fleet", "bar")
        .with_order("england", "nwy", "Support", aux="nth", target="ska")
        .with_order("england", "nth", "Move", target="ska")
        .with_order("russia", "swe", "Move", target="nwy")
        .with_order("russia", "ska", "Convoy", aux="swe", target="nwy")
        .with_order("russia", "bar", "Support", aux="swe", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Szykman: convoy fails; F SKA dislodged, A SWE stays.
    assert is_dislodged(result, "ska")
    assert has_unit(result, "russia", "Army", "swe")
    assert resolution_for(result, "swe") == "BOUNCE"


def test_g_12_swapping_two_units_with_two_convoys():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "lvp")
        .with_unit("england", "Fleet", "nao")
        .with_unit("england", "Fleet", "nrg")
        .with_unit("germany", "Army", "edi")
        .with_unit("germany", "Fleet", "nth")
        .with_unit("germany", "Fleet", "eng")
        .with_unit("germany", "Fleet", "iri")
        .with_order("england", "lvp", "Move", target="edi", via_convoy=True)
        .with_order("england", "nao", "Convoy", aux="lvp", target="edi")
        .with_order("england", "nrg", "Convoy", aux="lvp", target="edi")
        .with_order("germany", "edi", "Move", target="lvp", via_convoy=True)
        .with_order("germany", "nth", "Convoy", aux="edi", target="lvp")
        .with_order("germany", "eng", "Convoy", aux="edi", target="lvp")
        .with_order("germany", "iri", "Convoy", aux="edi", target="lvp")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "edi")
    assert has_unit(result, "germany", "Army", "lvp")


def test_g_13_support_cut_on_attack_on_itself_via_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("austria", "Fleet", "adr")
        .with_unit("austria", "Army", "tri")
        .with_unit("italy", "Army", "ven")
        .with_unit("italy", "Fleet", "alb")
        .with_order("austria", "adr", "Convoy", aux="tri", target="ven")
        .with_order("austria", "tri", "Move", target="ven", via_convoy=True)
        .with_order("italy", "ven", "Support", aux="alb", target="tri")
        .with_order("italy", "alb", "Move", target="tri")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Convoyed attack on VEN doesn't cut VEN's support of ALB-TRI (the
    # attacker comes "from" TRI which is the supported move's target).
    # F ALB-TRI dislodges A TRI.
    assert is_dislodged(result, "tri")
    assert has_unit(result, "italy", "Fleet", "tri")


def test_g_14_bounce_by_convoy_to_adjacent_province():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("england", "Fleet", "den")
        .with_unit("england", "Fleet", "fin")
        .with_unit("france", "Fleet", "nrg")
        .with_unit("france", "Fleet", "nth")
        .with_unit("germany", "Fleet", "ska")
        .with_unit("russia", "Army", "swe")
        .with_unit("russia", "Fleet", "bar")
        .with_order("england", "nwy", "Move", target="swe")
        .with_order("england", "den", "Support", aux="nwy", target="swe")
        .with_order("england", "fin", "Support", aux="nwy", target="swe")
        .with_order("france", "nrg", "Move", target="nwy")
        .with_order("france", "nth", "Support", aux="nrg", target="nwy")
        .with_order("germany", "ska", "Convoy", aux="swe", target="nwy")
        .with_order("russia", "swe", "Move", target="nwy", via_convoy=True)
        .with_order("russia", "bar", "Support", aux="swe", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # NOR-SWE attacks SWE with strength 3; A SWE is dislodged. SWE-NOR
    # and NRG-NOR mutually bounce.
    assert has_unit(result, "england", "Army", "swe")
    assert is_dislodged(result, "swe")
    assert resolution_for(result, "nrg") == "BOUNCE"


def test_g_15_bounce_and_dislodge_with_double_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "hol")
        .with_unit("england", "Army", "yor")
        .with_unit("england", "Army", "lon")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Army", "bel")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "hol", "Support", aux="lon", target="bel")
        .with_order("england", "yor", "Move", target="lon")
        .with_order("england", "lon", "Move", target="bel", via_convoy=True)
        .with_order("france", "eng", "Convoy", aux="bel", target="lon")
        .with_order("france", "bel", "Move", target="lon", via_convoy=True)
        .build()
    )

    result = adjudicate_one(variant, state)

    # A LON-BEL succeeds with support (dislodges A BEL). A BEL-LON bounces
    # against A YOR-LON.
    assert has_unit(result, "england", "Army", "bel")
    assert is_dislodged(result, "bel")
    assert resolution_for(result, "yor") == "BOUNCE"


def test_g_16_the_two_unit_in_one_area_bug_moving_by_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("england", "Army", "den")
        .with_unit("england", "Fleet", "bal")
        .with_unit("england", "Fleet", "nth")
        .with_unit("russia", "Army", "swe")
        .with_unit("russia", "Fleet", "ska")
        .with_unit("russia", "Fleet", "nrg")
        .with_order("england", "nwy", "Move", target="swe")
        .with_order("england", "den", "Support", aux="nwy", target="swe")
        .with_order("england", "bal", "Support", aux="nwy", target="swe")
        .with_order("england", "nth", "Move", target="nwy")
        .with_order("russia", "swe", "Move", target="nwy", via_convoy=True)
        .with_order("russia", "ska", "Convoy", aux="swe", target="nwy")
        .with_order("russia", "nrg", "Support", aux="swe", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # NOR-SWE succeeds (strength 3), SWE-NOR succeeds via convoy
    # (strength 2 > NTH-NOR's 1). NTH bounces.
    assert has_unit(result, "england", "Army", "swe")
    assert has_unit(result, "russia", "Army", "nwy")
    assert resolution_for(result, "nth") == "BOUNCE"


def test_g_17_the_two_unit_in_one_area_bug_moving_over_land():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Army", "nwy")
        .with_unit("england", "Army", "den")
        .with_unit("england", "Fleet", "bal")
        .with_unit("england", "Fleet", "ska")
        .with_unit("england", "Fleet", "nth")
        .with_unit("russia", "Army", "swe")
        .with_unit("russia", "Fleet", "nrg")
        .with_order("england", "nwy", "Move", target="swe", via_convoy=True)
        .with_order("england", "den", "Support", aux="nwy", target="swe")
        .with_order("england", "bal", "Support", aux="nwy", target="swe")
        .with_order("england", "ska", "Convoy", aux="nwy", target="swe")
        .with_order("england", "nth", "Move", target="nwy")
        .with_order("russia", "swe", "Move", target="nwy")
        .with_order("russia", "nrg", "Support", aux="swe", target="nwy")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Sweden and Norway swap; NTH bounces.
    assert has_unit(result, "england", "Army", "swe")
    assert has_unit(result, "russia", "Army", "nwy")
    assert resolution_for(result, "nth") == "BOUNCE"


def test_g_18_the_two_unit_in_one_area_bug_with_double_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "nth")
        .with_unit("england", "Army", "hol")
        .with_unit("england", "Army", "yor")
        .with_unit("england", "Army", "lon")
        .with_unit("england", "Army", "ruh")
        .with_unit("france", "Fleet", "eng")
        .with_unit("france", "Army", "bel")
        .with_unit("france", "Army", "wal")
        .with_order("england", "nth", "Convoy", aux="lon", target="bel")
        .with_order("england", "hol", "Support", aux="lon", target="bel")
        .with_order("england", "yor", "Move", target="lon")
        .with_order("england", "lon", "Move", target="bel", via_convoy=True)
        .with_order("england", "ruh", "Support", aux="lon", target="bel")
        .with_order("france", "eng", "Convoy", aux="bel", target="lon")
        .with_order("france", "bel", "Move", target="lon", via_convoy=True)
        .with_order("france", "wal", "Support", aux="bel", target="lon")
        .build()
    )

    result = adjudicate_one(variant, state)

    # Belgium and London swap; YOR fails.
    assert has_unit(result, "england", "Army", "bel")
    assert has_unit(result, "france", "Army", "lon")
    assert resolution_for(result, "yor") == "BOUNCE"


# === DATC 6.B: COASTAL ISSUES ===


def test_b_1_moving_with_unspecified_coast_when_coast_is_necessary():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "por")
        .with_order("france", "por", "Move", target="spa")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "por")
    assert resolution_for(result, "por") == "ILLEGAL"


def test_b_2_moving_with_unspecified_coast_when_coast_is_not_necessary():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "gas")
        .with_order("france", "gas", "Move", target="spa")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "spa/nc")
    assert resolution_for(result, "gas") == "OK"


def test_b_3_moving_with_wrong_coast_when_coast_is_not_necessary():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "gas")
        .with_order("france", "gas", "Move", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "gas")
    assert resolution_for(result, "gas") == "ILLEGAL"


def test_b_4_support_to_unreachable_coast_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "gas")
        .with_unit("france", "Fleet", "mar")
        .with_unit("italy", "Fleet", "wes")
        .with_order("france", "gas", "Move", target="spa/nc")
        .with_order("france", "mar", "Support", aux="gas", target="spa/nc")
        .with_order("italy", "wes", "Move", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "spa/nc")
    assert resolution_for(result, "gas") == "OK"
    assert resolution_for(result, "mar") == "OK"
    assert resolution_for(result, "wes") == "BOUNCE"


def test_b_5_support_from_unreachable_coast_not_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "mar")
        .with_unit("france", "Fleet", "spa/nc")
        .with_unit("italy", "Fleet", "lyo")
        .with_order("france", "mar", "Move", target="lyo")
        .with_order("france", "spa/nc", "Support", aux="mar", target="lyo")
        .with_order("italy", "lyo", "Hold")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Fleet", "lyo")
    assert not is_dislodged(result, "lyo")
    assert resolution_for(result, "spa/nc") == "ILLEGAL"
    assert resolution_for(result, "mar") == "BOUNCE"


def test_b_6_support_can_be_cut_with_other_coast():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("england", "Fleet", "iri")
        .with_unit("england", "Fleet", "nao")
        .with_unit("france", "Fleet", "spa/nc")
        .with_unit("france", "Fleet", "mao")
        .with_unit("italy", "Fleet", "lyo")
        .with_order("england", "iri", "Support", aux="nao", target="mao")
        .with_order("england", "nao", "Move", target="mao")
        .with_order("france", "spa/nc", "Support", aux="mao")
        .with_order("france", "mao", "Hold")
        .with_order("italy", "lyo", "Move", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "spa/nc") == "CUT"
    assert has_unit(result, "england", "Fleet", "mao")
    assert is_dislodged(result, "mao")


def test_b_7_supporting_own_unit_with_unspecified_coast():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "por")
        .with_unit("france", "Fleet", "mao")
        .with_unit("italy", "Fleet", "lyo")
        .with_unit("italy", "Fleet", "wes")
        .with_order("france", "por", "Support", aux="mao", target="spa")
        .with_order("france", "mao", "Move", target="spa/nc")
        .with_order("italy", "lyo", "Support", aux="wes", target="spa/sc")
        .with_order("italy", "wes", "Move", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "wes") == "BOUNCE"
    assert resolution_for(result, "mao") == "BOUNCE"


def test_b_8_supporting_with_unspecified_coast_when_only_one_coast_is_possible():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "por")
        .with_unit("france", "Fleet", "gas")
        .with_unit("italy", "Fleet", "lyo")
        .with_unit("italy", "Fleet", "wes")
        .with_order("france", "por", "Support", aux="gas", target="spa")
        .with_order("france", "gas", "Move", target="spa/nc")
        .with_order("italy", "lyo", "Support", aux="wes", target="spa/sc")
        .with_order("italy", "wes", "Move", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert resolution_for(result, "wes") == "BOUNCE"
    assert resolution_for(result, "gas") == "BOUNCE"


def test_b_9_supporting_with_wrong_coast():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "por")
        .with_unit("france", "Fleet", "mao")
        .with_unit("italy", "Fleet", "lyo")
        .with_unit("italy", "Fleet", "wes")
        .with_order("france", "por", "Support", aux="mao", target="spa/nc")
        .with_order("france", "mao", "Move", target="spa/sc")
        .with_order("italy", "lyo", "Support", aux="wes", target="spa/sc")
        .with_order("italy", "wes", "Move", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Fleet", "spa/sc")
    assert resolution_for(result, "mao") == "BOUNCE"


def test_b_10_unit_ordered_with_wrong_coast():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "spa/sc")
        .with_order("france", "spa/nc", "Move", target="lyo")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "lyo")
    assert resolution_for(result, "spa/sc") == "OK"


def test_b_11_coast_cannot_be_ordered_to_change():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Fleet", "spa/nc")
        .with_order("france", "spa/sc", "Move", target="lyo")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Fleet", "spa/nc")
    assert resolution_for(result, "spa/nc") == "ILLEGAL"


def test_b_12_army_movement_with_coastal_specification():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("france", "Army", "gas")
        .with_order("france", "gas", "Move", target="spa/nc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "france", "Army", "spa")
    assert resolution_for(result, "gas") == "OK"


def test_b_13_coastal_crawl_not_allowed():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Movement")
        .with_unit("turkey", "Fleet", "bul/sc")
        .with_unit("turkey", "Fleet", "con")
        .with_order("turkey", "bul/sc", "Move", target="con")
        .with_order("turkey", "con", "Move", target="bul/ec")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "turkey", "Fleet", "bul/sc")
    assert has_unit(result, "turkey", "Fleet", "con")
    assert resolution_for(result, "bul/sc") == "BOUNCE"
    assert resolution_for(result, "con") == "BOUNCE"


# === DATC 6.H: RETREATING ===


def test_h_1_no_supports_during_retreat():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("austria", "Fleet", "tri", dislodged=True, dislodged_from="tyr")
        .with_unit("austria", "Army", "ser")
        .with_unit("italy", "Army", "tri")
        .with_unit("turkey", "Fleet", "gre", dislodged=True, dislodged_from="ion")
        .with_unit("italy", "Fleet", "gre")
        .with_order("austria", "tri", "Retreat", target="alb")
        .with_order("austria", "ser", "Support", aux="tri", target="alb")
        .with_order("turkey", "gre", "Retreat", target="alb")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "austria", "Fleet", "alb")
    assert not has_unit(result, "turkey", "Fleet", "alb")
    assert not has_unit(result, "austria", "Fleet", "tri", dislodged=True)
    assert not has_unit(result, "turkey", "Fleet", "gre", dislodged=True)
    assert resolution_for(result, "tri") == "BOUNCE"
    assert resolution_for(result, "gre") == "BOUNCE"


def test_h_2_no_supports_from_retreating_unit():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Fleet", "nwy", dislodged=True, dislodged_from="fin")
        .with_unit("russia", "Army", "nwy")
        .with_unit("russia", "Fleet", "edi", dislodged=True, dislodged_from="lvp")
        .with_unit("england", "Army", "edi")
        .with_unit("russia", "Fleet", "hol", dislodged=True, dislodged_from="ruh")
        .with_unit("germany", "Army", "hol")
        .with_order("england", "nwy", "Retreat", target="nth")
        .with_order("russia", "edi", "Retreat", target="nth")
        .with_order("russia", "hol", "Support", aux="edi", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Fleet", "nth")
    assert not has_unit(result, "russia", "Fleet", "nth")
    assert resolution_for(result, "nwy") == "BOUNCE"
    assert resolution_for(result, "edi") == "BOUNCE"


def test_h_3_no_convoy_during_retreat():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Army", "hol", dislodged=True, dislodged_from="ruh")
        .with_unit("germany", "Army", "hol")
        .with_unit("england", "Fleet", "nth")
        .with_order("england", "hol", "Retreat", target="yor")
        .with_order("england", "nth", "Convoy", aux="hol", target="yor")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Army", "yor")
    assert resolution_for(result, "hol") == "ILLEGAL"


def test_h_4_no_other_moves_during_retreat():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Army", "hol", dislodged=True, dislodged_from="ruh")
        .with_unit("germany", "Army", "hol")
        .with_unit("england", "Fleet", "nth")
        .with_order("england", "hol", "Retreat", target="bel")
        .with_order("england", "nth", "Move", target="nrg")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "bel")
    assert has_unit(result, "england", "Fleet", "nth")


def test_h_5_a_unit_may_not_retreat_to_the_area_from_which_it_is_attacked():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("turkey", "Fleet", "ank", dislodged=True, dislodged_from="bla")
        .with_unit("russia", "Fleet", "ank")
        .with_order("turkey", "ank", "Retreat", target="bla")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "turkey", "Fleet", "bla")
    assert resolution_for(result, "ank") == "ILLEGAL"


def test_h_6_unit_may_not_retreat_to_a_contested_area():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("italy", "Army", "vie", dislodged=True, dislodged_from="tri")
        .with_unit("austria", "Army", "vie")
        .with_contested("boh")
        .with_order("italy", "vie", "Retreat", target="boh")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "italy", "Army", "boh")
    assert resolution_for(result, "vie") == "ILLEGAL"


def test_h_7_multiple_retreat_to_same_area_will_disband_units():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("italy", "Army", "vie", dislodged=True, dislodged_from="tri")
        .with_unit("italy", "Army", "boh", dislodged=True, dislodged_from="sil")
        .with_unit("austria", "Army", "vie")
        .with_unit("germany", "Army", "boh")
        .with_order("italy", "vie", "Retreat", target="tyr")
        .with_order("italy", "boh", "Retreat", target="tyr")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "italy", "Army", "tyr")
    assert resolution_for(result, "vie") == "BOUNCE"
    assert resolution_for(result, "boh") == "BOUNCE"


def test_h_8_triple_retreat_to_same_area_will_disband_units():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Fleet", "nwy", dislodged=True, dislodged_from="fin")
        .with_unit("russia", "Army", "nwy")
        .with_unit("russia", "Fleet", "edi", dislodged=True, dislodged_from="lvp")
        .with_unit("england", "Army", "edi")
        .with_unit("russia", "Fleet", "hol", dislodged=True, dislodged_from="ruh")
        .with_unit("germany", "Army", "hol")
        .with_order("england", "nwy", "Retreat", target="nth")
        .with_order("russia", "edi", "Retreat", target="nth")
        .with_order("russia", "hol", "Retreat", target="nth")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Fleet", "nth")
    assert not has_unit(result, "russia", "Fleet", "nth")
    assert resolution_for(result, "nwy") == "BOUNCE"
    assert resolution_for(result, "edi") == "BOUNCE"
    assert resolution_for(result, "hol") == "BOUNCE"


def test_h_9_dislodged_unit_will_not_make_attackers_area_contested():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("germany", "Fleet", "kie", dislodged=True, dislodged_from="hel")
        .with_unit("england", "Fleet", "kie")
        .with_unit("germany", "Army", "pru")
        .with_unit("germany", "Army", "sil")
        .with_unit("russia", "Army", "pru", dislodged=True, dislodged_from="ber")
        .with_order("germany", "kie", "Retreat", target="ber")
        .with_order("russia", "pru", "Disband")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "germany", "Fleet", "ber")
    assert resolution_for(result, "kie") == "OK"


def test_h_10_not_retreating_to_attacker_does_not_mean_contested():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Army", "kie", dislodged=True, dislodged_from="ber")
        .with_unit("germany", "Army", "kie")
        .with_unit("germany", "Army", "pru", dislodged=True, dislodged_from="war")
        .with_unit("russia", "Army", "pru")
        .with_order("england", "kie", "Retreat", target="ber")
        .with_order("germany", "pru", "Retreat", target="ber")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Army", "ber")
    assert has_unit(result, "germany", "Army", "ber")
    assert resolution_for(result, "kie") == "ILLEGAL"
    assert resolution_for(result, "pru") == "OK"


def test_h_11_retreat_when_dislodged_by_adjacent_convoy():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("italy", "Army", "mar", dislodged=True, dislodged_from=None)
        .with_unit("france", "Army", "mar")
        .with_order("italy", "mar", "Retreat", target="gas")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "italy", "Army", "gas")
    assert resolution_for(result, "mar") == "OK"


def test_h_12_retreat_when_dislodged_by_adjacent_convoy_while_trying_to_do_the_same():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Army", "lvp", dislodged=True, dislodged_from=None)
        .with_unit("russia", "Army", "lvp")
        .with_order("england", "lvp", "Retreat", target="edi")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert has_unit(result, "england", "Army", "edi")
    assert resolution_for(result, "lvp") == "OK"


def test_h_13_no_retreat_with_convoy_in_movement_phase():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Army", "pic", dislodged=True, dislodged_from="par")
        .with_unit("france", "Army", "pic")
        .with_unit("england", "Fleet", "eng")
        .with_order("england", "pic", "Retreat", target="lon")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Army", "lon")
    assert resolution_for(result, "pic") == "ILLEGAL"


def test_h_14_no_retreat_with_support_in_movement_phase():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Army", "pic", dislodged=True, dislodged_from="par")
        .with_unit("france", "Army", "pic")
        .with_unit("france", "Army", "bur", dislodged=True, dislodged_from="mar")
        .with_unit("germany", "Army", "bur")
        .with_order("england", "pic", "Retreat", target="bel")
        .with_order("france", "bur", "Retreat", target="bel")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Army", "bel")
    assert not has_unit(result, "france", "Army", "bel")
    assert resolution_for(result, "pic") == "BOUNCE"
    assert resolution_for(result, "bur") == "BOUNCE"


def test_h_15_no_coastal_crawl_in_retreat():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("england", "Fleet", "por", dislodged=True, dislodged_from="spa/sc")
        .with_unit("france", "Fleet", "por")
        .with_order("england", "por", "Retreat", target="spa/nc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "england", "Fleet", "spa/nc")
    assert resolution_for(result, "por") == "ILLEGAL"


def test_h_16_contested_for_both_coasts():
    variant = classical_variant()
    state = (
        StateBuilder(variant)
        .at_phase("Spring", 1901, "Retreat")
        .with_unit("france", "Fleet", "wes", dislodged=True, dislodged_from="tys")
        .with_unit("italy", "Fleet", "wes")
        .with_contested("spa")
        .with_order("france", "wes", "Retreat", target="spa/sc")
        .build()
    )

    result = adjudicate_one(variant, state)

    assert not has_unit(result, "france", "Fleet", "spa/sc")
    assert resolution_for(result, "wes") == "ILLEGAL"
