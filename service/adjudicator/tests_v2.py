"""
Tests for the prototype redesign of the adjudicator (engine_v2.py).

Each test constructs a small frozen `Variant` and a `State` via the
helpers in this file, invokes Engine.adjudicate, and asserts on the
resulting resolutions and post-resolution units.

The tests deliberately do NOT share fixtures with `tests.py` — that test
file targets the wire-format public surface through `adjudicate` /
`get_options`. Here we target the new Engine directly to demonstrate
the architecture's testability.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

import pytest

from .domain import (
    Adjacency,
    NamedCoast,
    Nation,
    Order as RawOrder,
    Phase,
    PhaseProgression,
    PhaseTransition,
    Province,
    ProvinceType,
    State,
    SupplyCenter,
    Unit,
    Variant,
)
from .engine_v2 import Engine, Status


# === Variant fixture ===

NORTH = "north"
SOUTH = "south"


def _province(
    pid: str,
    type_: str,
    *,
    sc: bool = False,
    home: Optional[str] = None,
    adj: Iterable[Adjacency] = (),
) -> Province:
    return Province(
        id=pid,
        name=pid.upper(),
        type=type_,
        supply_center=sc,
        home_nation=home,
        adjacencies=tuple(adj),
    )


def _named_coast(cid: str, parent: str, adj: Iterable[Adjacency]) -> NamedCoast:
    return NamedCoast(
        id=cid, name=cid.upper(), parent_province=parent, adjacencies=tuple(adj)
    )


def _edges(*pairs) -> dict:
    """Build a symmetric adjacency map from (a, b, pass_) triples. Each
    pair installs both directions automatically."""
    by_loc: dict = {}
    for a, b, p in pairs:
        by_loc.setdefault(a, []).append(Adjacency(to=b, pass_=p))
        by_loc.setdefault(b, []).append(Adjacency(to=a, pass_=p))
    return by_loc


def make_variant(*, allow_non_home: bool = False) -> Variant:
    """Construct the minimal test variant used across all engine_v2 tests.

    Provinces:
      - "lhs", "rhs", "ldd" : land. lhs and rhs are home SCs; ldd is a
        landlocked home SC of north (used for the fleet-in-landlocked
        build test).
      - "mid"               : coastal SC, no home nation (neutral SC).
      - "mlc"               : coastal SC, no home, with two named coasts
        (mlc/nc, mlc/sc) — used for the fleet-multi-coast test.
      - "iso", "far"        : coastal non-SC; iso is adjacent to mid,
        far is not adjacent to anywhere relevant.
      - "sea"               : sea province providing fleet adjacencies.

    The `allow_non_home` flag adds the adjudication modifier that
    permits builds in any owned supply center, exercising the
    BuildLocationIsHomeCenter check from both sides.
    """
    edges = _edges(
        ("lhs", "rhs", "both"),
        ("lhs", "mid", "both"),
        ("lhs", "sea", "fleet"),
        ("rhs", "mid", "both"),
        ("rhs", "sea", "fleet"),
        ("mid", "iso", "both"),
        ("mid", "sea", "fleet"),
        ("iso", "sea", "fleet"),
        ("ldd", "lhs", "army"),
        ("ldd", "rhs", "army"),
        ("mlc", "iso", "army"),
        ("mlc/nc", "sea", "fleet"),
        ("mlc/sc", "sea", "fleet"),
    )
    provinces = {
        "lhs": _province(
            "lhs", ProvinceType.LAND, sc=True, home=NORTH, adj=edges.get("lhs", ())
        ),
        "rhs": _province(
            "rhs", ProvinceType.LAND, sc=True, home=SOUTH, adj=edges.get("rhs", ())
        ),
        "mid": _province(
            "mid", ProvinceType.COASTAL, sc=True, home=None, adj=edges.get("mid", ())
        ),
        "ldd": _province(
            "ldd", ProvinceType.LAND, sc=True, home=NORTH, adj=edges.get("ldd", ())
        ),
        "mlc": _province(
            "mlc", ProvinceType.COASTAL, sc=True, home=NORTH, adj=edges.get("mlc", ())
        ),
        "iso": _province(
            "iso", ProvinceType.COASTAL, sc=False, adj=edges.get("iso", ())
        ),
        "far": _province(
            "far", ProvinceType.COASTAL, sc=False, adj=edges.get("far", ())
        ),
        "sea": _province(
            "sea", ProvinceType.SEA, sc=False, adj=edges.get("sea", ())
        ),
    }
    named_coasts = {
        "mlc/nc": _named_coast("mlc/nc", "mlc", edges.get("mlc/nc", ())),
        "mlc/sc": _named_coast("mlc/sc", "mlc", edges.get("mlc/sc", ())),
    }
    progression = PhaseProgression(
        seasons=("Spring",),
        transitions=(
            PhaseTransition(
                from_season="Spring",
                from_type=Phase.MOVEMENT,
                to_season="Spring",
                to_type=Phase.RETREAT,
                year_delta=0,
            ),
            PhaseTransition(
                from_season="Spring",
                from_type=Phase.RETREAT,
                to_season="Spring",
                to_type=Phase.ADJUSTMENT,
                year_delta=0,
            ),
            PhaseTransition(
                from_season="Spring",
                from_type=Phase.ADJUSTMENT,
                to_season="Spring",
                to_type=Phase.MOVEMENT,
                year_delta=1,
            ),
        ),
    )
    return Variant(
        id="test",
        name="Test",
        description="",
        author="",
        solo_victory_supply_centers=99,
        game_ends_year=None,
        draw_after_year=None,
        rules=None,
        adjudication_modifiers=(
            ("allow-builds-in-non-home-centers",) if allow_non_home else ()
        ),
        phase_progression=progression,
        nations=(
            Nation(id=NORTH, name="North", color="#000000"),
            Nation(id=SOUTH, name="South", color="#ffffff"),
        ),
        provinces=provinces,
        named_coasts=named_coasts,
        dominance_rules=(),
    )


def make_state(
    variant: Variant,
    *,
    phase_type: str,
    units: Iterable[Unit] = (),
    supply_centers: Iterable[SupplyCenter] = (),
    orders: Iterable[RawOrder] = (),
    contested: Iterable[str] = (),
) -> State:
    """Construct a fresh State for a single phase, with empty resolutions."""
    return State(
        variant=variant,
        phase=Phase(season="Spring", year=1901, type=phase_type),
        units=list(units),
        supply_centers=list(supply_centers),
        orders=list(orders),
        resolutions=None,
        skipped=False,
        outcome=None,
        contested_provinces=tuple(contested),
    )


def _resolution(states: List[State], province: str) -> Optional[str]:
    """Look up the resolution status for `province` in the first (resolved)
    state returned by the engine."""
    for r in states[0].resolutions or []:
        if r.province == province:
            return r.resolution
    return None


def _unit_at(states: List[State], location: str) -> Optional[Unit]:
    """Find a (non-dislodged) unit at `location` in the first state."""
    for u in states[0].units:
        if u.location == location and not u.dislodged:
            return u
    return None


# === Movement-phase tests ===


def test_movement_single_hold_resolves_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[RawOrder(nation=NORTH, source="lhs", order_type="Hold")],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _unit_at(result, "lhs") is not None


def test_movement_multiple_holds_all_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Hold"),
            RawOrder(nation=NORTH, source="mid", order_type="Hold"),
            RawOrder(nation=SOUTH, source="rhs", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "mid") == Status.OK
    assert _resolution(result, "rhs") == Status.OK


def test_movement_unordered_unit_defaults_to_hold_and_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _unit_at(result, "lhs") is not None


def test_move_to_adjacent_empty_province_succeeds():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "lhs") is None


def test_move_to_own_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="lhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL
    assert _unit_at(result, "lhs") is not None


def test_move_to_non_adjacent_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="far"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "far") is None


def test_two_moves_to_same_empty_province_both_bounce():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "rhs") == Status.BOUNCE
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "rhs") is not None


def test_move_into_holding_unit_bounces_and_holder_is_not_dislodged():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="mid", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "mid") is not None
    assert all(not u.dislodged for u in result[0].units)


def test_move_into_province_whose_occupant_moves_away_succeeds():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="mid", order_type="Move", target="iso"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "iso") is not None
    assert _unit_at(result, "lhs") is None
    assert all(not u.dislodged for u in result[0].units)


def test_move_into_province_whose_occupant_bounces_also_bounces():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mlc"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="mid", order_type="Move", target="iso"),
            RawOrder(nation=NORTH, source="mlc", order_type="Move", target="iso"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "mid") == Status.BOUNCE
    assert _resolution(result, "mlc") == Status.BOUNCE
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "mlc") is not None
    assert _unit_at(result, "iso") is None
    assert all(not u.dislodged for u in result[0].units)


def test_two_moves_bounce_target_parent_recorded_as_contested():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert len(result) == 2
    assert "mid" in result[1].contested_provinces


def test_hold_and_move_coexist_in_one_phase():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Hold"),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "rhs") == Status.OK
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "rhs") is None


# === Support, cuts, head-to-head, self-dislodgement, multi-way contests ===


def test_support_hold_at_own_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Support", aux="lhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL


def test_support_hold_with_no_supported_unit_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="rhs")],
        orders=[
            RawOrder(nation=NORTH, source="rhs", order_type="Support", aux="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.ILLEGAL


def test_support_hold_supporter_must_reach_supported():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="far"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="far", order_type="Support", aux="lhs"),
            RawOrder(nation=NORTH, source="lhs", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "far") == Status.ILLEGAL


def test_support_move_into_own_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            # rhs supports a move into its own province
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="rhs",
            ),
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="rhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.ILLEGAL


def test_support_move_with_no_supported_unit_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="rhs")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.ILLEGAL


def test_support_move_supporter_must_reach_target():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="far"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="far",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "far") == Status.ILLEGAL


def test_support_move_supported_must_reach_target():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            # Fleet at lhs can support to "sea" (fleet adjacency).
            Unit(nation=NORTH, type=Unit.FLEET, location="lhs"),
            # Army at rhs cannot move to "sea" (fleet-only adjacency).
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Support",
                aux="rhs",
                target="sea",
            ),
            RawOrder(nation=NORTH, source="rhs", order_type="Move", target="sea"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL


def test_legal_support_hold_resolves_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Hold"),
            RawOrder(nation=NORTH, source="rhs", order_type="Support", aux="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.OK
    assert _unit_at(result, "rhs") is not None


def test_legal_support_move_resolves_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.OK
    assert _resolution(result, "lhs") == Status.OK


def test_support_hold_for_moving_unit_is_unmatched():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            # An incoming attacker so the support is observably moot:
            # without the support the holder is still safe (strength 1
            # vs strength 1) but the support reports CUT (i.e. unmatched).
            Unit(nation=SOUTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Move", target="iso"),
            RawOrder(nation=NORTH, source="rhs", order_type="Support", aux="mid"),
            RawOrder(nation=SOUTH, source="lhs", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    # Mid is moving, so the SupportHold for it is unmatched -> CUT.
    assert _resolution(result, "rhs") == Status.CUT


def test_support_move_for_wrong_target_is_unmatched():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            # lhs is actually moving to mid, not rhs:
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            # but mid supports lhs->rhs:
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Support",
                aux="lhs",
                target="rhs",
            ),
            RawOrder(nation=SOUTH, source="rhs", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    # Support's claimed target (rhs) doesn't match lhs's actual target (mid).
    assert _resolution(result, "mid") == Status.CUT


def test_supported_move_dislodges_holder():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=SOUTH, source="mid", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "mid").nation == NORTH
    # Original mid occupant is dislodged.
    dislodged = [u for u in result[0].units if u.dislodged]
    assert len(dislodged) == 1
    assert dislodged[0].nation == SOUTH


def test_supported_move_beats_unsupported_competitor():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="iso"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=SOUTH, source="iso", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "iso") == Status.BOUNCE
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "mid").nation == NORTH


def test_attack_on_supporter_cuts_support():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
            # South fleet attacking the supporter from sea -> rhs.
            Unit(nation=SOUTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=SOUTH, source="mid", order_type="Hold"),
            RawOrder(nation=SOUTH, source="sea", order_type="Move", target="rhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.CUT
    # Support cut -> A has only strength 1 -> bounces vs holder.
    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _unit_at(result, "mid").nation == SOUTH


def test_bouncing_attack_still_cuts_support():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            # ldd holds at rhs's adjacency. The attacker from ldd will
            # bounce against the unit at rhs but still cut its support.
            Unit(nation=SOUTH, type=Unit.ARMY, location="ldd"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=SOUTH, source="ldd", order_type="Move", target="rhs"),
            RawOrder(nation=SOUTH, source="mid", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    # ldd's attack on rhs bounces (strength 1 vs hold 1) ...
    assert _resolution(result, "ldd") == Status.BOUNCE
    # ... but it still cuts the support.
    assert _resolution(result, "rhs") == Status.CUT
    assert _resolution(result, "lhs") == Status.BOUNCE


def test_attack_from_own_nation_does_not_cut():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            # Same-nation neighbour "attacking" the supporter does not cut.
            Unit(nation=NORTH, type=Unit.ARMY, location="ldd"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=NORTH, source="ldd", order_type="Move", target="rhs"),
            RawOrder(nation=SOUTH, source="mid", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "rhs") == Status.OK
    assert _resolution(result, "lhs") == Status.OK
    assert _unit_at(result, "mid").nation == NORTH


def test_support_move_not_cut_by_attack_from_target():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            # North attacks rhs supported from mid.
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            # South at rhs counter-attacks the supporter at mid.
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="rhs"),
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Support",
                aux="lhs",
                target="rhs",
            ),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    # Attack on the supporter comes from the support's target province
    # (rhs), so it does not cut the support.
    assert _resolution(result, "mid") == Status.OK
    assert _resolution(result, "lhs") == Status.OK
    # South bounces off the supporter at mid (1 vs 1).
    assert _resolution(result, "rhs") == Status.BOUNCE
    # The unit that successfully moved is North at rhs; the bounced South
    # army at rhs is dislodged by the supported move.
    assert _unit_at(result, "rhs").nation == NORTH


def test_support_hold_is_cut_by_any_foreign_attack():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Hold"),
            RawOrder(nation=NORTH, source="rhs", order_type="Support", aux="mid"),
            RawOrder(nation=SOUTH, source="lhs", order_type="Move", target="rhs"),
        ],
    )

    result = Engine().adjudicate(state)

    # SupportHold has no cut-from-target exception.
    assert _resolution(result, "rhs") == Status.CUT


def test_head_to_head_unsupported_both_bounce():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="rhs"),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="lhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "rhs") == Status.BOUNCE
    assert _unit_at(result, "lhs").nation == NORTH
    assert _unit_at(result, "rhs").nation == SOUTH


def test_head_to_head_supported_attacker_wins():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="rhs"),
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Support",
                aux="lhs",
                target="rhs",
            ),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="lhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "rhs") == Status.BOUNCE
    assert _unit_at(result, "rhs").nation == NORTH
    dislodged = [u for u in result[0].units if u.dislodged]
    assert len(dislodged) == 1
    assert dislodged[0].nation == SOUTH


def test_head_to_head_equally_supported_both_bounce():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="ldd"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="rhs"),
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Support",
                aux="lhs",
                target="rhs",
            ),
            RawOrder(nation=SOUTH, source="rhs", order_type="Move", target="lhs"),
            RawOrder(
                nation=SOUTH,
                source="ldd",
                order_type="Support",
                aux="rhs",
                target="lhs",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "rhs") == Status.BOUNCE
    assert all(not u.dislodged for u in result[0].units)


def test_self_attack_does_not_dislodge_even_with_overwhelming_strength():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            # Both attackers and defender are North.
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            # Supports from the same nation as the defender are dropped
            # for attack-strength; the move bounces regardless.
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=NORTH, source="mid", order_type="Hold"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "mid") == Status.OK
    assert all(not u.dislodged for u in result[0].units)


def test_self_attack_prevents_foreign_attack_from_succeeding():
    """DATC 6.E.6 — a self-attack still has prevent strength even though
    it cannot dislodge. Here a strong foreign attack that would otherwise
    succeed is held off by the self-attacker's prevent strength."""
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="iso"),
            Unit(nation=SOUTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            # North self-attack on mid (strength 1 against mid because
            # supports from the defender's own nation are dropped, but
            # prevent strength is 2 because the support still counts
            # there).
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=NORTH, source="mid", order_type="Hold"),
            # South attacks mid with strength 2.
            RawOrder(nation=SOUTH, source="iso", order_type="Move", target="mid"),
            RawOrder(
                nation=SOUTH,
                source="sea",
                order_type="Support",
                aux="iso",
                target="mid",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "iso") == Status.BOUNCE
    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid").nation == NORTH


def test_clean_three_cycle_all_succeed():
    """A→B→C→A with no other attackers — every move succeeds because
    each unit is moving into a province being vacated by the next."""
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="mid", order_type="Move", target="rhs"),
            RawOrder(nation=NORTH, source="rhs", order_type="Move", target="lhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "mid") == Status.OK
    assert _resolution(result, "rhs") == Status.OK
    assert _unit_at(result, "mid").nation == NORTH
    assert _unit_at(result, "rhs").nation == SOUTH
    assert _unit_at(result, "lhs").nation == NORTH
    assert all(not u.dislodged for u in result[0].units)


def test_three_attackers_one_supported_wins():
    """Three Moves into one province; the supported one (strength 2)
    beats both unsupported strength-1 competitors."""
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="iso"),
            Unit(nation=SOUTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=SOUTH, source="iso", order_type="Move", target="mid"),
            RawOrder(nation=SOUTH, source="sea", order_type="Move", target="mid"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "iso") == Status.BOUNCE
    assert _resolution(result, "sea") == Status.BOUNCE
    assert _unit_at(result, "mid").nation == NORTH


def test_two_equally_supported_attackers_both_bounce():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="iso"),
            Unit(nation=SOUTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="rhs",
                order_type="Support",
                aux="lhs",
                target="mid",
            ),
            RawOrder(nation=SOUTH, source="iso", order_type="Move", target="mid"),
            RawOrder(
                nation=SOUTH,
                source="sea",
                order_type="Support",
                aux="iso",
                target="mid",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "iso") == Status.BOUNCE
    assert _unit_at(result, "mid") is None


# === Retreat-phase tests ===


def test_retreat_to_adjacent_empty_province_is_ok_and_unit_moves():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Retreat", target="iso"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "iso") is not None
    assert _unit_at(result, "mid") is None


def test_retreat_to_non_adjacent_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Retreat", target="far"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL
    assert _unit_at(result, "far") is None


def test_retreat_to_occupied_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
            Unit(nation=SOUTH, type=Unit.ARMY, location="iso"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Retreat", target="iso"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL


def test_retreat_to_attacker_origin_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Retreat", target="lhs"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL


def test_retreat_to_contested_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Retreat", target="iso"),
        ],
        contested=("iso",),
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL


def test_two_retreats_to_same_parent_both_bounce():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
            Unit(
                nation=SOUTH,
                type=Unit.ARMY,
                location="mlc",
                dislodged=True,
                dislodged_from="rhs",
            ),
        ],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Retreat", target="iso"),
            RawOrder(nation=SOUTH, source="mlc", order_type="Retreat", target="iso"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.BOUNCE
    assert _resolution(result, "mlc") == Status.BOUNCE
    assert _unit_at(result, "iso") is None


def test_disband_order_removes_unit():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
        ],
        orders=[RawOrder(nation=NORTH, source="mid", order_type="Disband")],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is None
    # No standing unit anywhere.
    assert all(not u.dislodged for u in result[0].units)
    assert len(result[0].units) == 0


def test_unordered_dislodged_unit_defaults_to_disband():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.RETREAT,
        units=[
            Unit(
                nation=NORTH,
                type=Unit.ARMY,
                location="mid",
                dislodged=True,
                dislodged_from="lhs",
            ),
        ],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is None
    assert len(result[0].units) == 0


# === Adjustment-phase tests ===


def test_build_at_home_supply_center_is_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Build",
                target="lhs",
                unit_type=Unit.ARMY,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _unit_at(result, "lhs") is not None


def test_build_at_non_supply_center_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="iso",
                order_type="Build",
                target="iso",
                unit_type=Unit.ARMY,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "iso") == Status.ILLEGAL


def test_build_at_unowned_supply_center_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            # mid is a SC but unowned by north.
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Build",
                target="mid",
                unit_type=Unit.ARMY,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL


def test_build_at_non_home_center_without_modifier_is_illegal():
    variant = make_variant(allow_non_home=False)
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[
            SupplyCenter(nation=NORTH, province="lhs"),
            SupplyCenter(nation=NORTH, province="mid"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Build",
                target="mid",
                unit_type=Unit.ARMY,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL


def test_build_at_non_home_center_with_modifier_is_ok():
    variant = make_variant(allow_non_home=True)
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[
            SupplyCenter(nation=NORTH, province="lhs"),
            SupplyCenter(nation=NORTH, province="mid"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Build",
                target="mid",
                unit_type=Unit.ARMY,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is not None


def test_build_at_occupied_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        supply_centers=[
            SupplyCenter(nation=NORTH, province="lhs"),
            SupplyCenter(nation=NORTH, province="ldd"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Build",
                target="lhs",
                unit_type=Unit.ARMY,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL


def test_second_build_at_same_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[
            SupplyCenter(nation=NORTH, province="lhs"),
            SupplyCenter(nation=NORTH, province="ldd"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Build",
                target="lhs",
                unit_type=Unit.ARMY,
            ),
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Build",
                target="lhs",
                unit_type=Unit.ARMY,
            ),
        ],
    )

    result = Engine().adjudicate(state)

    resolutions = result[0].resolutions
    assert resolutions is not None
    assert resolutions[0].resolution == Status.OK
    assert resolutions[1].resolution == Status.ILLEGAL


def test_fleet_build_in_landlocked_province_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[SupplyCenter(nation=NORTH, province="ldd")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="ldd",
                order_type="Build",
                target="ldd",
                unit_type=Unit.FLEET,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "ldd") == Status.ILLEGAL


def test_fleet_build_at_multi_coast_without_coast_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[],
        supply_centers=[SupplyCenter(nation=NORTH, province="mlc")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="mlc",
                order_type="Build",
                target="mlc",
                unit_type=Unit.FLEET,
            )
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mlc") == Status.ILLEGAL


def test_excess_builds_beyond_allowed_are_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        # 1 owned SC, 0 units -> allowed = 1; submit 2 builds; second fails.
        units=[],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Build",
                target="lhs",
                unit_type=Unit.ARMY,
            ),
            RawOrder(
                nation=NORTH,
                source="ldd",
                order_type="Build",
                target="ldd",
                unit_type=Unit.ARMY,
            ),
        ],
    )

    result = Engine().adjudicate(state)

    resolutions = result[0].resolutions
    assert resolutions is not None
    assert resolutions[0].resolution == Status.OK
    assert resolutions[1].resolution == Status.ILLEGAL


# === Adjustment-phase disband tests ===


def test_disband_with_one_unit_surplus_removes_unit():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[RawOrder(nation=NORTH, source="mid", order_type="Disband")],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "lhs") is not None


def test_disband_with_two_unit_surplus_removes_two_units():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="iso"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Disband"),
            RawOrder(nation=NORTH, source="iso", order_type="Disband"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _resolution(result, "iso") == Status.OK
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "iso") is None
    assert _unit_at(result, "lhs") is not None


def test_disband_for_unowned_unit_is_illegal_and_civil_disorder_fills_gap():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
        ],
        supply_centers=[
            SupplyCenter(nation=NORTH, province="lhs"),
            SupplyCenter(nation=SOUTH, province="rhs"),
        ],
        orders=[RawOrder(nation=NORTH, source="rhs", order_type="Disband")],
    )

    result = Engine().adjudicate(state)

    resolutions = result[0].resolutions or []
    # The disband targets a unit owned by another nation — ILLEGAL.
    # Civil disorder still fills the required disband by removing mid.
    rhs = next(r for r in resolutions if r.province == "rhs")
    assert rhs.resolution == Status.ILLEGAL
    mid = next(r for r in resolutions if r.province == "mid")
    assert mid.resolution == Status.OK
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "rhs") is not None


def test_second_disband_for_same_unit_is_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Disband"),
            RawOrder(nation=NORTH, source="mid", order_type="Disband"),
        ],
    )

    result = Engine().adjudicate(state)

    resolutions = result[0].resolutions
    assert resolutions is not None
    assert resolutions[0].resolution == Status.OK
    assert resolutions[1].resolution == Status.ILLEGAL


def test_excess_disbands_beyond_required_are_illegal():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="mid", order_type="Disband"),
            RawOrder(nation=NORTH, source="lhs", order_type="Disband"),
        ],
    )

    result = Engine().adjudicate(state)

    resolutions = result[0].resolutions
    assert resolutions is not None
    assert resolutions[0].resolution == Status.OK
    assert resolutions[1].resolution == Status.ILLEGAL


# === Civil-disorder tests ===


def test_civil_disorder_one_surplus_no_orders_removes_furthest_unit():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "lhs") is not None


def test_civil_disorder_two_surplus_no_orders_removes_two_furthest_units():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="iso"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.OK
    assert _resolution(result, "iso") == Status.OK
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "iso") is None
    assert _unit_at(result, "lhs") is not None


def test_civil_disorder_fills_partial_disband_submission():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="iso"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[RawOrder(nation=NORTH, source="mid", order_type="Disband")],
    )

    result = Engine().adjudicate(state)

    # Submitted disband: mid.
    assert _resolution(result, "mid") == Status.OK
    # Civil disorder picks the farthest non-disbanded unit: iso.
    assert _resolution(result, "iso") == Status.OK
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "iso") is None
    assert _unit_at(result, "lhs") is not None


def test_civil_disorder_with_no_owned_supply_centers_removes_all_units():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
        ],
        supply_centers=[],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "mid") == Status.OK
    assert _unit_at(result, "lhs") is None
    assert _unit_at(result, "mid") is None
    assert len(result[0].units) == 0


def test_civil_disorder_ranks_fleet_before_army_on_distance_tie():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        # Owned SC = mid. lhs (army) and sea (fleet) are both adjacent
        # to mid → both at distance 1. Fleet should be removed first.
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="mid")],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.OK
    assert _unit_at(result, "sea") is None
    assert _unit_at(result, "lhs") is not None


def test_civil_disorder_breaks_type_ties_alphabetically_by_location():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        # Owned SC = mid. lhs and iso are both adjacent to mid (distance 1).
        # Both armies; alphabetical: "iso" < "lhs" so iso is removed first.
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="iso"),
        ],
        supply_centers=[SupplyCenter(nation=NORTH, province="mid")],
        orders=[],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "iso") == Status.OK
    assert _unit_at(result, "iso") is None
    assert _unit_at(result, "lhs") is not None


def test_adjustment_phase_mixes_builds_explicit_disbands_and_civil_disorder():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        # North: 1 SC (lhs), 0 units. Builds 1 unit at lhs.
        # South: 1 SC (rhs), 3 units. Required disbands = 2.
        #   Submits Disband at mid; civil disorder removes the
        #   farthest remaining: iso (distance 2 from rhs).
        units=[
            Unit(nation=SOUTH, type=Unit.ARMY, location="rhs"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="mid"),
            Unit(nation=SOUTH, type=Unit.ARMY, location="iso"),
        ],
        supply_centers=[
            SupplyCenter(nation=NORTH, province="lhs"),
            SupplyCenter(nation=SOUTH, province="rhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Build",
                target="lhs",
                unit_type=Unit.ARMY,
            ),
            RawOrder(nation=SOUTH, source="mid", order_type="Disband"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "mid") == Status.OK
    assert _resolution(result, "iso") == Status.OK
    assert _unit_at(result, "lhs") is not None
    assert _unit_at(result, "rhs") is not None
    assert _unit_at(result, "mid") is None
    assert _unit_at(result, "iso") is None


# === Engine error tests ===


def test_engine_raises_for_unsupported_phase_type():
    variant = make_variant()
    state = make_state(variant, phase_type="UnknownPhase")

    with pytest.raises(NotImplementedError):
        Engine().adjudicate(state)


def test_engine_silently_drops_cross_phase_movement_order_type():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[
            RawOrder(
                nation=NORTH, source="lhs", order_type="Retreat", target="mid"
            ),
        ],
    )

    states = Engine().adjudicate(state)

    # The cross-phase order is dropped; the unit gets a default Hold and resolves OK.
    assert _resolution(states, "lhs") == Status.OK
    assert _unit_at(states, "lhs") is not None


def test_engine_silently_drops_cross_phase_adjustment_order_type():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.ADJUSTMENT,
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        supply_centers=[SupplyCenter(nation=NORTH, province="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Support", target="mid"),
        ],
    )

    # The cross-phase order is dropped; no parsed orders, no resolutions, unit kept.
    states = Engine().adjudicate(state)
    assert states[0].resolutions == []
    assert any(u.location == "lhs" for u in states[0].units)
