from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import jsonschema
import yaml

from .domain import (
    Adjacency,
    DominanceDependency,
    DominanceRule,
    NamedCoast,
    Nation,
    Order,
    OrderOption,
    Outcome,
    Pass,
    Phase,
    PhaseProgression,
    PhaseTransition,
    Province,
    Resolution,
    State,
    SupplyCenter,
    Unit,
    Variant,
)


SUPPORTED_PHASE_TYPES = frozenset({Phase.MOVEMENT, Phase.RETREAT, Phase.ADJUSTMENT})
SUPPORTED_UNIT_TYPES = frozenset({Unit.ARMY, Unit.FLEET})
SUPPORTED_ORDER_TYPES = frozenset(
    {"Move", "Hold", "Support", "Convoy", "Build", "Disband", "Retreat"}
)


class VariantValidationError(ValueError):
    pass


class GameStateValidationError(ValueError):
    pass


_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}


def _schema_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "variant.schema.yaml"))


def _load_schema() -> Dict[str, Any]:
    path = _schema_path()
    if path not in _SCHEMA_CACHE:
        with open(path, "r") as f:
            _SCHEMA_CACHE[path] = yaml.safe_load(f)
    return _SCHEMA_CACHE[path]


def _validate_against_schema(data: Dict[str, Any]) -> None:
    schema = _load_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        path = ".".join(str(p) for p in exc.absolute_path) or "<root>"
        raise VariantValidationError(f"Variant schema violation at {path}: {exc.message}") from exc


def _validate_adjacency_symmetry(
    provinces: Dict[str, Province], named_coasts: Dict[str, NamedCoast]
) -> None:
    edges: Dict[str, str] = {}

    def add(source_id: str, target_id: str, pass_value: str) -> None:
        key = f"{source_id}->{target_id}:{pass_value}"
        edges[key] = pass_value

    for province in provinces.values():
        for adjacency in province.adjacencies:
            add(province.id, adjacency.to, adjacency.pass_)
    for named_coast in named_coasts.values():
        for adjacency in named_coast.adjacencies:
            add(named_coast.id, adjacency.to, adjacency.pass_)

    for province in provinces.values():
        for adjacency in province.adjacencies:
            mirror_key = f"{adjacency.to}->{province.id}:{adjacency.pass_}"
            if mirror_key not in edges:
                raise VariantValidationError(
                    f"Adjacency {province.id} -> {adjacency.to} ({adjacency.pass_}) "
                    f"is not mirrored on the other side"
                )

    for named_coast in named_coasts.values():
        for adjacency in named_coast.adjacencies:
            mirror_key = f"{adjacency.to}->{named_coast.id}:{adjacency.pass_}"
            if mirror_key not in edges:
                raise VariantValidationError(
                    f"Adjacency {named_coast.id} -> {adjacency.to} ({adjacency.pass_}) "
                    f"is not mirrored on the other side"
                )


def deserialize_variant(data: Dict[str, Any]) -> Variant:
    _validate_against_schema(data)

    nations = tuple(
        Nation(id=n["id"], name=n["name"], color=n["color"]) for n in data["nations"]
    )

    provinces: Dict[str, Province] = {}
    for p in data["provinces"]:
        adjacencies = tuple(
            Adjacency(to=a["to"], pass_=a["pass"]) for a in p["adjacencies"]
        )
        provinces[p["id"]] = Province(
            id=p["id"],
            name=p["name"],
            type=p["type"],
            supply_center=p["supplyCenter"],
            home_nation=p.get("homeNation"),
            adjacencies=adjacencies,
        )

    named_coasts: Dict[str, NamedCoast] = {}
    for nc in data.get("namedCoasts", []):
        adjacencies = tuple(
            Adjacency(to=a["to"], pass_=a["pass"]) for a in nc["adjacencies"]
        )
        if any(a.pass_ != Pass.FLEET for a in adjacencies):
            raise VariantValidationError(
                f"Named coast {nc['id']} has non-fleet adjacency"
            )
        named_coasts[nc["id"]] = NamedCoast(
            id=nc["id"],
            name=nc["name"],
            parent_province=nc["parentProvince"],
            adjacencies=adjacencies,
        )

    _validate_adjacency_symmetry(provinces, named_coasts)

    pp = data["phaseProgression"]
    phase_progression = PhaseProgression(
        seasons=tuple(pp["seasons"]),
        transitions=tuple(
            PhaseTransition(
                from_season=t["from"]["season"],
                from_type=t["from"]["type"],
                to_season=t["to"]["season"],
                to_type=t["to"]["type"],
                year_delta=t["to"]["yearDelta"],
            )
            for t in pp["transitions"]
        ),
    )

    dominance_rules = tuple(
        DominanceRule(
            province=r["province"],
            nation=r["nation"],
            priority=r["priority"],
            dependencies=tuple(
                DominanceDependency(province=d["province"], nation=d["nation"])
                for d in r["dependencies"]
            ),
        )
        for r in data.get("dominanceRules", [])
    )

    seen_priority: Dict[str, set] = {}
    for rule in dominance_rules:
        bucket = seen_priority.setdefault(rule.province, set())
        if rule.priority in bucket:
            raise VariantValidationError(
                f"Duplicate dominance rule priority {rule.priority} for province {rule.province}"
            )
        bucket.add(rule.priority)

    return Variant(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        author=data["author"],
        solo_victory_supply_centers=data["soloVictorySupplyCenters"],
        game_ends_year=data.get("gameEndsYear"),
        draw_after_year=data.get("drawAfterYear"),
        rules=data.get("rules"),
        adjudication_modifiers=tuple(data.get("adjudicationModifiers", [])),
        phase_progression=phase_progression,
        nations=nations,
        provinces=provinces,
        named_coasts=named_coasts,
        dominance_rules=dominance_rules,
    )


def _validate_phase(variant: Variant, phase_data: Dict[str, Any]) -> Phase:
    season = phase_data["season"]
    type_ = phase_data["type"]
    if season not in variant.phase_progression.seasons:
        raise GameStateValidationError(f"Unknown season: {season!r}")
    if type_ not in SUPPORTED_PHASE_TYPES:
        raise GameStateValidationError(f"Unsupported phase type: {type_!r}")
    return Phase(season=season, year=phase_data["year"], type=type_)


def _validate_location(variant: Variant, location: str) -> None:
    if location not in variant.provinces and location not in variant.named_coasts:
        raise GameStateValidationError(f"Unknown location: {location!r}")


def _validate_nation(variant: Variant, nation_id: str) -> None:
    if not any(n.id == nation_id for n in variant.nations):
        raise GameStateValidationError(f"Unknown nation: {nation_id!r}")


def deserialize_game_state(data: Dict[str, Any], variant: Variant) -> State:
    if "phase" not in data:
        raise GameStateValidationError("Missing 'phase' field")
    phase = _validate_phase(variant, data["phase"])

    units: List[Unit] = []
    for u in data.get("units", []):
        if u["type"] not in SUPPORTED_UNIT_TYPES:
            raise GameStateValidationError(f"Unsupported unit type: {u['type']!r}")
        _validate_nation(variant, u["nation"])
        _validate_location(variant, u["location"])
        units.append(
            Unit(
                nation=u["nation"],
                type=u["type"],
                location=u["location"],
                dislodged=bool(u.get("dislodged", False)),
            )
        )

    supply_centers: List[SupplyCenter] = []
    for sc in data.get("supplyCenters", []):
        _validate_nation(variant, sc["nation"])
        if sc["province"] not in variant.provinces:
            raise GameStateValidationError(f"Unknown supply-center province: {sc['province']!r}")
        if not variant.provinces[sc["province"]].supply_center:
            raise GameStateValidationError(
                f"Province {sc['province']} is not a supply center"
            )
        supply_centers.append(
            SupplyCenter(nation=sc["nation"], province=sc["province"])
        )

    orders: List[Order] = []
    for o in data.get("orders", []):
        if o["orderType"] not in SUPPORTED_ORDER_TYPES:
            raise GameStateValidationError(f"Unsupported order type: {o['orderType']!r}")
        _validate_nation(variant, o["nation"])
        orders.append(
            Order(
                nation=o["nation"],
                source=o["source"],
                order_type=o["orderType"],
                target=o.get("target"),
                aux=o.get("aux"),
                unit_type=o.get("unitType"),
                via_convoy=bool(o.get("viaConvoy", False)),
            )
        )

    resolutions_raw = data.get("resolutions")
    if resolutions_raw is None:
        resolutions: Optional[List[Resolution]] = None
    else:
        resolutions = [
            Resolution(
                province=r["province"],
                resolution=r["resolution"],
                reason=r.get("reason"),
            )
            for r in resolutions_raw
        ]

    outcome_raw = data.get("outcome")
    outcome: Optional[Outcome]
    if outcome_raw is None:
        outcome = None
    else:
        outcome = Outcome(
            winners=tuple(outcome_raw["winners"]),
            reason=outcome_raw["reason"],
            year=outcome_raw["year"],
        )

    return State(
        variant=variant,
        phase=phase,
        units=units,
        supply_centers=supply_centers,
        orders=orders,
        resolutions=resolutions,
        skipped=bool(data.get("skipped", False)),
        outcome=outcome,
    )


def serialize_game_state(state: State) -> Dict[str, Any]:
    return {
        "phase": {
            "season": state.phase.season,
            "year": state.phase.year,
            "type": state.phase.type,
        },
        "units": [
            {
                "nation": u.nation,
                "type": u.type,
                "location": u.location,
                "dislodged": u.dislodged,
            }
            for u in state.units
        ],
        "supplyCenters": [
            {"nation": sc.nation, "province": sc.province} for sc in state.supply_centers
        ],
        "orders": [
            {
                "nation": o.nation,
                "source": o.source,
                "orderType": o.order_type,
                "target": o.target,
                "aux": o.aux,
                "unitType": o.unit_type,
                "viaConvoy": o.via_convoy,
            }
            for o in state.orders
        ],
        "resolutions": (
            None
            if state.resolutions is None
            else [
                {
                    "province": r.province,
                    "resolution": r.resolution,
                    "reason": r.reason,
                }
                for r in state.resolutions
            ]
        ),
        "skipped": state.skipped,
        "outcome": (
            None
            if state.outcome is None
            else {
                "winners": list(state.outcome.winners),
                "reason": state.outcome.reason,
                "year": state.outcome.year,
            }
        ),
    }


def serialize_options(options: List[OrderOption]) -> List[Dict[str, Any]]:
    return [
        {
            "source": opt.source,
            "orderType": opt.order_type,
            "target": opt.target,
            "aux": opt.aux,
            "unitType": opt.unit_type,
            "namedCoast": opt.named_coast,
        }
        for opt in options
    ]
