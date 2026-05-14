"""
Tests for the C2 increment: convoyed-move legality (un-marking by
MarkConvoyedMovesReachable) and convoy matching (MatchConvoys).

C2 wires convoyed moves into legality and computes the convoy_matched
flag on each non-ILLEGAL ConvoyOrder. Convoy disruption (matched
convoys whose fleets are cut) is C3's job — the resolver still treats
convoyed moves as if they were directly adjacent once they pass
legality. Tests here focus on:

  - the un-marking step: a coastal-to-coastal Move whose direct
    reachability fails is re-examined and un-marked when a static
    convoy path exists through the submitted non-ILLEGAL ConvoyOrders;
  - the matching step: convoy_matched is True/False/None for matched,
    unmatched, and ILLEGAL ConvoyOrders respectively;
  - pipeline ordering: directly adjacent moves are unaffected by
    un-marking; convoy_matched persists through the rest of the
    pipeline.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from .domain import (
    Adjacency,
    Nation,
    Order as RawOrder,
    Phase,
    PhaseProgression,
    PhaseTransition,
    Province,
    ProvinceType,
    State,
    Unit,
    Variant,
)
from .engine_v2 import Actions, Engine, MovementPhaseResolver
from .types import (
    AdjudicationState,
    ConvoyOrder,
    MoveOrder,
    Status,
)
from .tests_v2 import NORTH, SOUTH, make_state, make_variant


# === Helpers ===


def _movement_state(units, orders) -> State:
    """Spring 1901 Movement-phase state on the standard test variant."""
    return make_state(
        make_variant(),
        phase_type=Phase.MOVEMENT,
        units=units,
        orders=orders,
    )


def _resolution(states: List[State], province: str) -> Optional[str]:
    for r in states[0].resolutions or []:
        if r.province == province:
            return r.resolution
    return None


def _failure_reason(states: List[State], province: str) -> Optional[str]:
    for r in states[0].resolutions or []:
        if r.province == province:
            return r.reason
    return None


def _unit_at(states: List[State], location: str) -> Optional[Unit]:
    for u in states[0].units:
        if u.location == location and not u.dislodged:
            return u
    return None


def _adjudicate_to_completion(state: State) -> AdjudicationState:
    """Run the full Movement-phase pipeline and return the final
    AdjudicationState so tests can inspect internal fields like
    convoy_matched. Mirrors Engine.adjudicate but returns the inner
    frozen state instead of building external State(s)."""
    engine = Engine()
    adj = engine._to_adjudication_state(state)
    for action in MovementPhaseResolver.actions_for(adj):
        adj = engine.dispatch(adj, action)
    return adj


def _convoy_matched_at(adj: AdjudicationState, source: str) -> Optional[bool]:
    """Return the convoy_matched value for the ConvoyOrder at `source`,
    or None if no ConvoyOrder is parsed there."""
    for order, res in zip(adj.parsed_orders, adj.resolutions):
        if isinstance(order, ConvoyOrder) and order.source == source:
            return res.convoy_matched
    return None


# === Custom chain variant for multi-sea path tests ===


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


def _edges(*pairs) -> dict:
    by_loc: dict = {}
    for a, b, p in pairs:
        by_loc.setdefault(a, []).append(Adjacency(to=b, pass_=p))
        by_loc.setdefault(b, []).append(Adjacency(to=a, pass_=p))
    return by_loc


def make_chain_variant() -> Variant:
    """Variant with three sea provinces forming a chain between two
    coastal land provinces:

        a -- sea1 -- sea2 -- sea3 -- b

    `a` and `b` are coastal land provinces with no army-passable edge
    between them; an army move a -> b requires a convoy. The chain
    permits tests of multi-fleet convoys and tests where a fleet at one
    sea province is not adjacent to one of the endpoints."""
    edges = _edges(
        ("a", "sea1", "fleet"),
        ("b", "sea3", "fleet"),
        ("sea1", "sea2", "fleet"),
        ("sea2", "sea3", "fleet"),
    )
    provinces = {
        "a": _province(
            "a", ProvinceType.LAND, sc=True, home=NORTH, adj=edges.get("a", ())
        ),
        "b": _province(
            "b", ProvinceType.LAND, sc=True, home=SOUTH, adj=edges.get("b", ())
        ),
        "sea1": _province(
            "sea1", ProvinceType.SEA, adj=edges.get("sea1", ())
        ),
        "sea2": _province(
            "sea2", ProvinceType.SEA, adj=edges.get("sea2", ())
        ),
        "sea3": _province(
            "sea3", ProvinceType.SEA, adj=edges.get("sea3", ())
        ),
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
        id="chain",
        name="Chain",
        description="",
        author="",
        solo_victory_supply_centers=99,
        game_ends_year=None,
        draw_after_year=None,
        rules=None,
        adjudication_modifiers=(),
        phase_progression=progression,
        nations=(
            Nation(id=NORTH, name="North", color="#000000"),
            Nation(id=SOUTH, name="South", color="#ffffff"),
        ),
        provinces=provinces,
        named_coasts={},
        dominance_rules=(),
    )


# === Convoyed move legality (positive cases) ===


def test_single_sea_convoyed_move_resolves_ok():
    """Army at lhs, fleet at sea adjacent to both lhs and iso, fleet
    Convoy(lhs->iso), army Move(lhs->iso). The Move is reachability-
    illegal directly (lhs and iso share no army edge) but un-marked by
    MarkConvoyedMovesReachable. Final status: OK; convoy matched."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="iso"),
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

    assert _resolution(result, "lhs") == Status.OK
    assert _resolution(result, "sea") == Status.OK
    assert _unit_at(result, "iso") is not None
    assert _unit_at(result, "lhs") is None


def test_single_sea_convoy_is_matched():
    """Same scenario as above; assert the internal convoy_matched flag."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="iso"),
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="iso",
            ),
        ],
    )

    adj = _adjudicate_to_completion(state)

    assert _convoy_matched_at(adj, "sea") is True


def test_chain_convoyed_move_resolves_ok():
    """Three sea provinces forming a chain between coasts a and b.
    Fleets at sea1, sea2, sea3 all order matching Convoys; army at a
    moves to b. The full chain is needed; with all three fleets
    ordering Convoys the static path exists end-to-end."""
    variant = make_chain_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="a"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea1"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea2"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea3"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="a", order_type="Move", target="b"),
            RawOrder(
                nation=NORTH, source="sea1", order_type="Convoy", aux="a", target="b"
            ),
            RawOrder(
                nation=NORTH, source="sea2", order_type="Convoy", aux="a", target="b"
            ),
            RawOrder(
                nation=NORTH, source="sea3", order_type="Convoy", aux="a", target="b"
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "a") == Status.OK
    assert _resolution(result, "sea1") == Status.OK
    assert _resolution(result, "sea2") == Status.OK
    assert _resolution(result, "sea3") == Status.OK
    assert _unit_at(result, "b") is not None
    assert _unit_at(result, "a") is None


# === Convoyed move legality (negative cases) ===


def test_convoyed_move_with_no_convoy_orders_is_illegal():
    """Army moves coastal-to-coastal with no ConvoyOrders submitted at
    all. Reachability fails directly and un-marking finds no matching
    convoy fleets, so the move stays ILLEGAL with the original
    reachability message."""
    state = _movement_state(
        units=[Unit(nation=NORTH, type=Unit.ARMY, location="lhs")],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="iso"),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.ILLEGAL
    assert _failure_reason(result, "lhs") == "The unit can't reach the target province."
    assert _unit_at(result, "lhs") is not None


def test_convoyed_move_with_path_not_existing_is_illegal():
    """Chain variant: army at a moves to b, but only sea3's fleet has a
    matching Convoy. The path requires sea1 and sea2 as well; without
    fleets there, no static path exists and the move stays ILLEGAL.
    The lone Convoy at sea3 is well-formed (passes legality) but
    convoy_matched is False because the Move it would carry never
    becomes non-ILLEGAL."""
    variant = make_chain_variant()
    state = make_state(
        variant,
        phase_type=Phase.MOVEMENT,
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="a"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea3"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="a", order_type="Move", target="b"),
            RawOrder(
                nation=NORTH, source="sea3", order_type="Convoy", aux="a", target="b"
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "a") == Status.ILLEGAL
    assert _failure_reason(result, "a") == "The unit can't reach the target province."
    assert _resolution(result, "sea3") == Status.OK

    adj = _adjudicate_to_completion(state)
    assert _convoy_matched_at(adj, "sea3") is False


def test_convoyed_move_with_mismatched_convoy_bounces_and_convoy_unmatched():
    """Army at lhs moves to iso. A second army at mid is ordered to
    Hold. The fleet at sea orders Convoy(mid->iso) — well-formed
    (army at mid exists; both endpoints coastal) but the endpoints
    don't match the lhs->iso move. A fleet sits in a sea province
    capable of convoying lhs->iso, so the move is treated as a failed
    convoy (DATC 6.D.32 vs 6.D.8): legal-but-bouncing, with the
    convoy unmatched for this army's endpoints."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.ARMY, location="mid"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="iso"),
            RawOrder(nation=NORTH, source="mid", order_type="Hold"),
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="mid",
                target="iso",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.BOUNCE
    assert _resolution(result, "sea") == Status.OK

    adj = _adjudicate_to_completion(state)
    assert _convoy_matched_at(adj, "sea") is False


# === Convoy matching ===


def test_convoy_with_matching_move_is_matched():
    """Army at lhs orders Move to iso. Fleet at sea orders Convoy
    matching the move. After MatchConvoys, convoy_matched is True."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="iso"),
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="iso",
            ),
        ],
    )

    adj = _adjudicate_to_completion(state)

    assert _convoy_matched_at(adj, "sea") is True


def test_convoy_without_matching_move_is_unmatched_but_resolves_ok():
    """Army at lhs holds; fleet at sea orders Convoy(lhs->iso). The
    army never moves, so no MoveOrder matches the convoy. Convoy is
    unmatched (convoy_matched=False) but its final status is OK — an
    unmatched convoy is a no-op, not a CUT-equivalent."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Hold"),
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
    adj = _adjudicate_to_completion(state)

    assert _resolution(result, "sea") == Status.OK
    assert _convoy_matched_at(adj, "sea") is False


def test_illegal_convoy_has_convoy_matched_none():
    """A Convoy that fails legality (e.g. a fleet on a coastal
    province) is ILLEGAL. Its convoy_matched stays None — the matcher
    skips ILLEGAL convoys."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.FLEET, location="mid"),
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="iso"),
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
    adj = _adjudicate_to_completion(state)

    assert _resolution(result, "mid") == Status.ILLEGAL
    assert _convoy_matched_at(adj, "mid") is None


# === Pipeline ordering ===


def test_directly_adjacent_move_is_unaffected_by_unmarking():
    """A Move whose target is directly adjacent passes legality
    cleanly. Even with a Convoy chain available for the same endpoints,
    un-marking is a no-op for this move because its status was never
    ILLEGAL. The move resolves OK via the direct adjacency path."""
    state = _movement_state(
        units=[
            Unit(nation=NORTH, type=Unit.ARMY, location="lhs"),
            Unit(nation=NORTH, type=Unit.FLEET, location="sea"),
        ],
        orders=[
            RawOrder(nation=NORTH, source="lhs", order_type="Move", target="mid"),
            RawOrder(
                nation=NORTH,
                source="sea",
                order_type="Convoy",
                aux="lhs",
                target="mid",
            ),
        ],
    )

    result = Engine().adjudicate(state)

    assert _resolution(result, "lhs") == Status.OK
    assert _unit_at(result, "mid") is not None
    assert _unit_at(result, "lhs") is None
