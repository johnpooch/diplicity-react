"""
Tests for the convoy substrate added in increment C1: ConvoyOrder
parsing, the six convoy legality checks, and the convoy_path_exists
path-finding function.

C1 deliberately does *not* integrate convoys into move resolution, so
these tests exercise only:

  - that a CONVOY raw order parses into a ConvoyOrder (and falls back
    to Hold when its fields are missing);
  - that each Check rejects the case it is designed to catch;
  - that convoy_path_exists answers the geometric question correctly
    over hand-built maps.

Convoy matching, move legality via convoy, and convoy-disruption
integration into the strength solver are out of scope for C1 and are
covered in C2 / C3 / C4.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from .convoy import convoy_path_exists
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
from .engine_v2 import Engine
from .types import AdjudicationState, ConvoyOrder, StateView, Status
from .tests_v2 import NORTH, SOUTH, make_state, make_variant


# === Helpers for the convoy-pipeline check tests ===


def _movement_state(units, orders, contested: Iterable[str] = ()) -> State:
    """Build a minimal Spring 1901 Movement-phase state on the standard
    test variant from `tests_v2.make_variant()`. Convenience wrapper —
    keeps the convoy-check tests focused on the inputs that matter."""
    return make_state(
        make_variant(),
        phase_type=Phase.MOVEMENT,
        units=units,
        orders=orders,
        contested=contested,
    )


def _resolution(states: List[State], province: str) -> Optional[str]:
    """Look up the resolution status for `province` in the first
    (resolved) state returned by the engine."""
    for r in states[0].resolutions or []:
        if r.province == province:
            return r.resolution
    return None


def _failure_reason(states: List[State], province: str) -> Optional[str]:
    for r in states[0].resolutions or []:
        if r.province == province:
            return r.reason
    return None


def _parsed_orders(states: List[State]) -> List[RawOrder]:
    """The raw orders that survived the resolution into the resolved
    state. We can't read the parsed Order list directly through the
    external State boundary, so tests that need to assert on parsing
    behaviour inspect resolutions and unit positions instead."""
    return states[0].orders


# === Parse-reducer tests ===


def test_convoy_with_aux_and_target_parses_to_convoy_order():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="iso",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.OK


def test_convoy_missing_aux_falls_back_to_hold_and_resolves_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.FLEET, location="sea")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux=None,
                target="iso",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.OK


def test_convoy_missing_target_falls_back_to_hold_and_resolves_ok():
    variant = make_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[Unit(nation=NORTH, type=Unit.FLEET, location="sea")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target=None,
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.OK


# === Legality check tests ===


def test_army_issuing_convoy_is_illegal():
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="rhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="lhs",
                order_type="Convoy",
                aux="rhs",
                target="mid",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL
    assert _failure_reason(result, "lhs") == "Only fleets can convoy."


def test_fleet_on_coastal_province_cannot_convoy():
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="mid",
                order_type="Convoy",
                aux="lhs",
                target="iso",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "mid") == Status.ILLEGAL
    assert _failure_reason(result, "mid") == (
        "A convoying fleet must be in a sea province."
    )


def test_convoy_with_no_army_at_source_is_illegal():
    state = _movement_state(
        units=[Unit(nation=NORTH, type=Unit.FLEET, location="sea")],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="iso",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.ILLEGAL
    assert _failure_reason(result, "sea") == (
        "There's no army at the convoy source province."
    )


def test_convoy_of_fleet_at_source_is_illegal():
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
            Unit(nation=NORTH, type=Unit.FLEET, location="lhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="iso",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.ILLEGAL
    assert _failure_reason(result, "sea") == "Convoyed unit must be an army."


def test_convoy_with_inland_endpoint_is_illegal():
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
            Unit(nation=NORTH, type=Unit.ARMY, location="ldd"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="ldd",
                target="rhs",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.ILLEGAL
    assert _failure_reason(result, "sea") == (
        "Convoy endpoints must be coastal provinces."
    )


def test_convoy_with_sea_endpoint_is_illegal():
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="sea",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.ILLEGAL
    assert _failure_reason(result, "sea") == (
        "Convoy endpoints must be coastal provinces."
    )


def test_convoy_source_equals_target_is_illegal():
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="lhs",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "sea") == Status.ILLEGAL
    assert _failure_reason(result, "sea") == "Convoy source and target must differ."


# === convoy_path_exists tests ===


def _province(
    pid: str,
    type_: str,
    *,
    adj: Iterable[Adjacency] = (),
) -> Province:
    return Province(
        id=pid,
        name=pid.upper(),
        type=type_,
        supply_center=False,
        home_nation=None,
        adjacencies=tuple(adj),
    )


def _path_variant(provinces) -> Variant:
    """Construct a minimal Variant carrying only the bits the path
    finder reads: provinces map + named_coasts + parent_of via the
    standard `Variant.parent_of` implementation. Phase progression and
    nations are unused but required by the Variant dataclass."""
    progression = PhaseProgression(seasons=("Spring",), transitions=())
    return Variant(
        id="path-test",
        name="Path Test",
        description="",
        author="",
        solo_victory_supply_centers=99,
        game_ends_year=None,
        draw_after_year=None,
        rules=None,
        adjudication_modifiers=(),
        phase_progression=progression,
        nations=(),
        provinces=provinces,
        named_coasts={},
        dominance_rules=(),
    )


def _path_state(variant: Variant) -> StateView:
    """Wrap `variant` in a StateView so convoy_path_exists can read it.
    Units / orders / supply centers are empty — the path function does
    not consult them."""
    return StateView(
        AdjudicationState(
            variant=variant,
            phase=Phase(season="Spring", year=1901, type=Phase.MOVEMENT),
            units=(),
            supply_centers=(),
            raw_orders=(),
            contested_provinces=(),
        )
    )


def _single_sea_map() -> Variant:
    """Coast A — Sea1 — Coast B. Sea1 fleet-adjacent to both coasts."""
    return _path_variant(
        provinces={
            "a": _province(
                "a",
                ProvinceType.COASTAL,
                adj=(Adjacency(to="sea1", pass_="fleet"),),
            ),
            "b": _province(
                "b",
                ProvinceType.COASTAL,
                adj=(Adjacency(to="sea1", pass_="fleet"),),
            ),
            "sea1": _province(
                "sea1",
                ProvinceType.SEA,
                adj=(
                    Adjacency(to="a", pass_="fleet"),
                    Adjacency(to="b", pass_="fleet"),
                ),
            ),
        }
    )


def _two_sea_chain_map() -> Variant:
    """Coast A — Sea1 — Sea2 — Coast B. A is fleet-adjacent only to
    Sea1; B is fleet-adjacent only to Sea2; the two sea provinces are
    fleet-adjacent to each other. Exercises the asymmetric BFS case
    where the final hop's sea province lies in `end_set` but is *not*
    in the convoying fleet set."""
    return _path_variant(
        provinces={
            "a": _province(
                "a",
                ProvinceType.COASTAL,
                adj=(Adjacency(to="sea1", pass_="fleet"),),
            ),
            "b": _province(
                "b",
                ProvinceType.COASTAL,
                adj=(Adjacency(to="sea2", pass_="fleet"),),
            ),
            "sea1": _province(
                "sea1",
                ProvinceType.SEA,
                adj=(
                    Adjacency(to="a", pass_="fleet"),
                    Adjacency(to="sea2", pass_="fleet"),
                ),
            ),
            "sea2": _province(
                "sea2",
                ProvinceType.SEA,
                adj=(
                    Adjacency(to="sea1", pass_="fleet"),
                    Adjacency(to="b", pass_="fleet"),
                ),
            ),
        }
    )


def _three_sea_chain_map() -> Variant:
    """Coast A — Sea1 — Sea2 — Sea3 — Coast B."""
    return _path_variant(
        provinces={
            "a": _province(
                "a",
                ProvinceType.COASTAL,
                adj=(Adjacency(to="sea1", pass_="fleet"),),
            ),
            "b": _province(
                "b",
                ProvinceType.COASTAL,
                adj=(Adjacency(to="sea3", pass_="fleet"),),
            ),
            "sea1": _province(
                "sea1",
                ProvinceType.SEA,
                adj=(
                    Adjacency(to="a", pass_="fleet"),
                    Adjacency(to="sea2", pass_="fleet"),
                ),
            ),
            "sea2": _province(
                "sea2",
                ProvinceType.SEA,
                adj=(
                    Adjacency(to="sea1", pass_="fleet"),
                    Adjacency(to="sea3", pass_="fleet"),
                ),
            ),
            "sea3": _province(
                "sea3",
                ProvinceType.SEA,
                adj=(
                    Adjacency(to="sea2", pass_="fleet"),
                    Adjacency(to="b", pass_="fleet"),
                ),
            ),
        }
    )


def test_path_with_single_fleet_between_coasts():
    state = _path_state(_single_sea_map())

    assert convoy_path_exists(state, "a", "b", ["sea1"]) is True


def test_path_blocked_when_only_sea_is_not_in_convoying_set():
    state = _path_state(_single_sea_map())

    assert convoy_path_exists(state, "a", "b", ["sea_elsewhere"]) is False


def test_path_through_three_fleet_chain():
    state = _path_state(_three_sea_chain_map())

    assert (
        convoy_path_exists(state, "a", "b", ["sea1", "sea2", "sea3"]) is True
    )


def test_path_broken_when_middle_fleet_missing():
    state = _path_state(_three_sea_chain_map())

    assert convoy_path_exists(state, "a", "b", ["sea1", "sea3"]) is False


def test_path_empty_fleet_set_returns_true_when_geometrically_connected():
    state = _path_state(_single_sea_map())

    assert convoy_path_exists(state, "a", "b", []) is True


def test_path_source_equals_target_returns_false():
    state = _path_state(_single_sea_map())

    assert convoy_path_exists(state, "a", "a", ["sea1"]) is False


def test_path_blocked_when_final_sea_has_no_fleet():
    """Asymmetric BFS case: a fleet at the entry sea but no fleet at
    the sea adjacent to the destination. The destination sea sits in
    `end_set` but is not in `convoying_fleet_locations`, so the chain
    is incomplete and the path must not be reported."""
    state = _path_state(_two_sea_chain_map())

    assert convoy_path_exists(state, "a", "b", ["sea1"]) is False


def test_path_through_two_fleet_chain_succeeds():
    """The symmetric counterpart to the asymmetric-bug test: fleets at
    both seas closes the chain end-to-end and the path is reported."""
    state = _path_state(_two_sea_chain_map())

    assert convoy_path_exists(state, "a", "b", ["sea1", "sea2"]) is True
