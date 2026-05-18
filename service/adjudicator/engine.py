from __future__ import annotations

# === Imports ===
from dataclasses import dataclass, replace
from typing import ClassVar, Dict, List, Tuple, Type

from .convoy import convoy_path_exists, is_convoy_redundant
from .domain import (
    Phase,
    Resolution,
    State,
    SupplyCenter,
    Unit,
)
from .resolution import resolve_strengths_and_cuts
from .types import (
    ALLOW_NON_HOME_BUILDS,
    Action,
    AdjudicationState,
    AdjustmentDisbandOrder,
    BuildOrder,
    Check,
    ConvoyOrder,
    DisbandOrder,
    HoldOrder,
    MoveOrder,
    MoveTargetIsReachableCheck,
    Order,
    OrderResolution,
    OrderType,
    RetreatOrder,
    StateView,
    Status,
    SupportHoldOrder,
    SupportMoveOrder,
)


# === Actions ===


class Actions:
    """Namespace of action classes. Each inner class describes a single
    state transition; the matching `Reducer` subclass (paired via its
    ACTION attribute) performs it. Empty action classes still carry
    semantic meaning as named transitions even though they have no
    payload."""

    @dataclass(frozen=True)
    class ParseMovementOrders(Action):
        """Phase-1 Movement parse: each non-dislodged unit gets a HoldOrder
        (its own if submitted, else a default Hold). Non-Hold order types
        raise NotImplementedError — outside the prototype slice."""

    @dataclass(frozen=True)
    class ParseRetreatOrders(Action):
        """Phase-1 Retreat parse: each dislodged unit gets a RetreatOrder
        or DisbandOrder (default Disband if no order submitted)."""

    @dataclass(frozen=True)
    class ParseAdjustmentOrders(Action):
        """Phase-1 Adjustment parse: each Build order becomes a BuildOrder.
        Disband orders raise NotImplementedError — adjustment-phase disband
        is out of scope for the prototype."""

    @dataclass(frozen=True)
    class ApplyLegalityChecks(Action):
        """For each parsed order in submission order, run its LEGALITY_CHECKS
        against the input state and mark the first failing check's MESSAGE
        on the order. Checks are pure predicates over the input state — they
        do not depend on the resolutions of other orders in the same phase."""

    @dataclass(frozen=True)
    class MarkRedundantConvoysIllegal(Action):
        """Movement-phase: a Convoy whose fleet sits on a longer-than-
        minimum chain through the submitted matching ConvoyOrders is
        redundant — it doesn't contribute to delivering the army any
        faster than a shorter chain would. Such convoys are marked
        ILLEGAL (DATC 6.G.19, 6.F.12) so they neither express own-
        nation intent nor count toward the matched-convoy chain in
        resolution. Convoys that are reachable but on no current chain
        (DATC 6.G.6) are not redundant — they're just useless intent,
        legal but ineffective."""

    @dataclass(frozen=True)
    class MarkConvoyedMovesReachable(Action):
        """Movement-phase: decide which Army Move orders are *via convoy*.

        Two cases:
        (1) Reachability — a Move flagged ILLEGAL by MoveTargetIsReachable
            because direct adjacency does not connect the endpoints is
            re-examined as a convoyed move. If the endpoints are coastal
            and any standing fleets in sea provinces could form a chain,
            the Move is un-marked (legal but via_convoy). Whether matched
            convoys actually deliver it is decided in resolution
            (CONVOY_PATH_INTACT).
        (2) Intent — a Move that *is* directly reachable still travels by
            convoy when the player either set the via_convoy flag on the
            raw order or when an own-nation Fleet has issued a matching
            Convoy order (DATC 6.G.1/6.G.5). Marking via_convoy here is
            what disables head-to-head detection for the move, enabling
            the "swap by convoy" outcome."""

    @dataclass(frozen=True)
    class EnforceUniqueAdjustmentTargets(Action):
        """Adjustment-phase: for each parent province, keep the first
        still-undecided BuildOrder or AdjustmentDisbandOrder targeting it
        and mark all later orders at the same parent ILLEGAL. Builds and
        disbands are tracked separately — a Build at LON and a Disband at
        LON do not conflict at this stage (different categories of order;
        the legality checks already rule out the impossible cases like
        building onto an occupied square)."""

    @dataclass(frozen=True)
    class MatchSupports(Action):
        """Movement-phase: walk parsed Support orders and decide which ones
        are *matched* — i.e. the supported unit is actually doing what the
        support claims. SupportHold matches a unit that exists and is not
        ordered into a non-ILLEGAL Move; SupportMove matches a non-ILLEGAL
        MoveOrder whose target equals the support's claimed target
        (parent-province match accepted). Writes support_matched."""

    @dataclass(frozen=True)
    class MatchConvoys(Action):
        """Movement-phase: walk parsed Convoy orders and decide which ones
        are *matched* — i.e. there is a non-ILLEGAL MoveOrder from the
        convoy's army_source to its army_target. Writes convoy_matched.
        ILLEGAL Convoys are left as None — they contribute no convoy
        capacity regardless. The result depends only on parsed_orders
        and the ILLEGAL marks set by ApplyLegalityChecks /
        MarkConvoyedMovesReachable; no iteration is needed."""

    @dataclass(frozen=True)
    class ResolveStrengthsAndCuts(Action):
        """Movement-phase: invoke the strength-and-cut solver (resolution.py)
        which simultaneously computes support cuts, attack / defense /
        prevent / hold strengths, and Move statuses. The solver uses an
        explicit Decision graph with tracked dependencies and cycle
        detection (DATC 6.D, 6.E, 6.G, 6.F.4)."""

    @dataclass(frozen=True)
    class ResolveRetreatBounces(Action):
        """Retreat-phase: when two or more legal retreats target the same
        parent province, all of them resolve to BOUNCE (DATC 6.H.7/8)."""

    @dataclass(frozen=True)
    class EnforceBuildLimits(Action):
        """Adjustment-phase: for each nation, mark the first N still-undecided
        builds as OK (where N is the allowed build count for that nation)
        and any further builds as ILLEGAL with a too-many message."""

    @dataclass(frozen=True)
    class EnforceDisbandLimits(Action):
        """Adjustment-phase: for each nation, mark the first N still-undecided
        AdjustmentDisbandOrders as OK (where N is the required disband
        count for that nation) and any further disbands as ILLEGAL with a
        too-many message."""

    @dataclass(frozen=True)
    class ApplyCivilDisorder(Action):
        """Adjustment-phase: for each nation with a unit surplus, count
        still-undecided AdjustmentDisbandOrders against the required
        disband total and, if short, select additional units via the
        civil-disorder ranking to fill the gap. Selected locations are
        recorded on state.civil_disorder_disbands for the outcomes
        reducer to consume."""

    @dataclass(frozen=True)
    class FinalizeStatuses(Action):
        """Any order still without a status resolves to OK."""

    @dataclass(frozen=True)
    class ApplyMovementOutcomes(Action):
        """Compute the Movement-phase post-resolution units list and the
        set of contested provinces, then drop any dislodged unit with
        no legal retreat (auto-disband). For Hold-only, this is just
        the input units."""

    @dataclass(frozen=True)
    class ApplyRetreatOutcomes(Action):
        """Compute the Retreat-phase post-resolution units list: standing
        units kept, successful retreats relocated, all other dislodged
        units removed, dislodged flags cleared."""

    @dataclass(frozen=True)
    class UpdateSupplyCenterOwnership(Action):
        """Retreat-phase: recompute supply-center ownership for the next
        phase. When the next phase is an Adjustment phase, ownership is
        recounted from the post-retreat unit positions — every
        supply-center province occupied by a unit transfers to that
        unit's nation, and unoccupied supply centers keep their current
        owner. When the next phase is not an Adjustment phase, current
        ownership is carried through unchanged. Writes
        next_supply_centers."""

    @dataclass(frozen=True)
    class ApplyAdjustmentOutcomes(Action):
        """Compute the Adjustment-phase post-resolution units list:
        existing units kept, OK builds appended as new units."""


# === Reducers ===


_REDUCER_REGISTRY: Dict[Type[Action], Type["Reducer"]] = {}


class Reducer:
    """Base class for reducers. A Reducer is paired with exactly one
    Action class via the ACTION class attribute, and provides a single
    `reduce` classmethod that transforms state.

    Subclasses are auto-registered into the reducer registry when the
    class body is evaluated, via __init_subclass__. There is no need
    to decorate subclasses — declaring the ACTION attribute is enough.
    """

    ACTION: ClassVar[Type[Action]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "ACTION"):
            _REDUCER_REGISTRY[cls.ACTION] = cls

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        """Transform state in response to action. Subclasses override.
        Receives a StateView; returns a StateView (typically constructed
        via state.replace(...))."""
        raise NotImplementedError


class ParseMovementOrdersReducer(Reducer):
    """Populate parsed_orders with one Order per standing unit. A submitted
    Hold / Move / Support / Convoy raw order for a unit replaces the
    default Hold; units without a submitted order get a default HoldOrder.
    A SUPPORT raw order with no `aux` falls back to Hold. A CONVOY raw
    order with no `aux` or no `target` falls back to Hold. Raw orders of
    a type that doesn't belong to the Movement phase (Retreat, Disband,
    Build) are silently dropped — DATC convention is to ignore garbage
    orders rather than refuse to adjudicate."""

    ACTION = Actions.ParseMovementOrders

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        standing = state.units().standing_by_loc()
        units_view = state.units()
        variant = state.variant()
        by_loc: Dict[str, Order] = {}
        via_convoy_by_loc: Dict[str, bool] = {}
        for raw in state.raw_orders():
            if raw.order_type not in (
                OrderType.HOLD,
                OrderType.MOVE,
                OrderType.SUPPORT,
                OrderType.CONVOY,
            ):
                continue
            unit = units_view.at_parent(raw.source or "")
            if (
                unit is None
                or unit.nation != raw.nation
                or unit.location in by_loc
            ):
                continue
            if raw.order_type == OrderType.MOVE and raw.target is not None:
                if raw.via_convoy:
                    via_convoy_by_loc[unit.location] = True
                # Named-coast normalization: armies ignore named coasts
                # (DATC 6.B.12); fleets ordered to a bare parent with
                # named coasts auto-select the unique reachable coast
                # (DATC 6.B.2).
                target = raw.target
                target_parent = variant.parent_of(target)
                if unit.type == Unit.ARMY and target != target_parent:
                    target = target_parent
                elif unit.type == Unit.FLEET and target == target_parent:
                    coasts = variant.coasts_of(target_parent)
                    if coasts:
                        reachable = [
                            c for c in coasts
                            if variant.can_move(unit.location, c, Unit.FLEET)
                        ]
                        if len(reachable) == 1:
                            target = reachable[0]
                by_loc[unit.location] = MoveOrder(
                    nation=unit.nation,
                    source=unit.location,
                    target=target,
                    unit_type=unit.type,
                )
            elif raw.order_type == OrderType.SUPPORT and raw.aux is not None:
                # A Support is a support-to-hold when the supported unit is
                # not moving — encoded either as target=None or as
                # target == aux (godip: support targets [supporter, supportee]
                # with from == to). Only target != aux is a support-to-move.
                if raw.target is None or raw.target == raw.aux:
                    by_loc[unit.location] = SupportHoldOrder(
                        nation=unit.nation,
                        source=unit.location,
                        supported_source=raw.aux,
                        unit_type=unit.type,
                    )
                else:
                    by_loc[unit.location] = SupportMoveOrder(
                        nation=unit.nation,
                        source=unit.location,
                        supported_source=raw.aux,
                        target=raw.target,
                        unit_type=unit.type,
                    )
            elif (
                raw.order_type == OrderType.CONVOY
                and raw.aux is not None
                and raw.target is not None
            ):
                by_loc[unit.location] = ConvoyOrder(
                    nation=unit.nation,
                    source=unit.location,
                    army_source=raw.aux,
                    army_target=raw.target,
                    unit_type=unit.type,
                )
            else:
                by_loc[unit.location] = HoldOrder(
                    nation=unit.nation, source=unit.location, unit_type=unit.type
                )
        for loc, unit in standing.items():
            by_loc.setdefault(
                loc, HoldOrder(nation=unit.nation, source=loc, unit_type=unit.type)
            )
        sorted_locs = sorted(by_loc)
        parsed = tuple(by_loc[loc] for loc in sorted_locs)
        resolutions = tuple(
            OrderResolution(via_convoy=via_convoy_by_loc.get(loc, False))
            for loc in sorted_locs
        )
        return state.replace(parsed_orders=parsed, resolutions=resolutions)



class ParseRetreatOrdersReducer(Reducer):
    """Populate parsed_orders with one RetreatOrder or DisbandOrder per
    dislodged unit. Submitted orders win; unaccompanied dislodged units
    default to Disband (DATC convention). Raw orders of a type that
    doesn't belong to the Retreat phase (Hold, Move, Support, Convoy,
    Build) are silently dropped — DATC convention is to ignore garbage
    orders rather than refuse to adjudicate. A Retreat raw order with
    no target falls back to Disband for that unit."""

    ACTION = Actions.ParseRetreatOrders

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        units = state.units()
        dislodged = units.dislodged_by_loc()
        by_loc: Dict[str, Order] = {}
        for raw in state.raw_orders():
            if raw.order_type not in (OrderType.RETREAT, OrderType.DISBAND):
                continue
            unit = units.dislodged_for_source(raw.source or "")
            if unit is None or unit.nation != raw.nation or unit.location in by_loc:
                continue
            if raw.order_type == OrderType.RETREAT and raw.target is not None:
                by_loc[unit.location] = RetreatOrder(
                    nation=unit.nation,
                    source=unit.location,
                    target=raw.target,
                    unit_type=unit.type,
                    dislodged_from=unit.dislodged_from,
                )
            else:
                by_loc[unit.location] = DisbandOrder(
                    nation=unit.nation, source=unit.location, unit_type=unit.type
                )
        for loc, unit in dislodged.items():
            by_loc.setdefault(
                loc, DisbandOrder(nation=unit.nation, source=loc, unit_type=unit.type)
            )
        parsed = tuple(by_loc[loc] for loc in sorted(by_loc))
        return state.replace(
            parsed_orders=parsed,
            resolutions=tuple(OrderResolution() for _ in parsed),
        )


class ParseAdjustmentOrdersReducer(Reducer):
    """Populate parsed_orders with one BuildOrder per Build raw order and
    one AdjustmentDisbandOrder per Disband raw order, in submission order.
    Disbands targeting a location without a matching standing unit are
    still parsed — `AdjustmentDisbandUnitExistsCheck` will mark them
    ILLEGAL during legality checking, which keeps the resolution visible
    to players. Raw orders of a type that doesn't belong to the Adjustment
    phase (Hold, Move, Support, Convoy, Retreat) are silently dropped —
    DATC convention is to ignore garbage orders rather than refuse to
    adjudicate."""

    ACTION = Actions.ParseAdjustmentOrders

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        standing = state.units().standing_by_loc()
        parsed: List[Order] = []
        for raw in state.raw_orders():
            if raw.order_type == OrderType.BUILD:
                location = raw.target if raw.target is not None else (raw.source or "")
                parsed.append(
                    BuildOrder(
                        nation=raw.nation, location=location, unit_type=raw.unit_type
                    )
                )
                continue
            if raw.order_type == OrderType.DISBAND:
                source = raw.source or ""
                unit = standing.get(source)
                unit_type = unit.type if unit is not None else (raw.unit_type or "")
                parsed.append(
                    AdjustmentDisbandOrder(
                        nation=raw.nation, location=source, unit_type=unit_type
                    )
                )
                continue
        return state.replace(
            parsed_orders=tuple(parsed),
            resolutions=tuple(OrderResolution() for _ in parsed),
        )


class ApplyLegalityChecksReducer(Reducer):
    """Walk parsed_orders in index order and apply each order's
    LEGALITY_CHECKS against the input state. The first failing check's
    MESSAGE becomes the order's failure_reason; its status becomes
    ILLEGAL. Checks are pure predicates over the input state and do not
    see the resolutions of other orders in this phase."""

    ACTION = Actions.ApplyLegalityChecks

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        resolutions = list(state.resolutions())
        for i, order in enumerate(state.parsed_orders()):
            if resolutions[i].status is not None:
                continue
            for check_cls in order.LEGALITY_CHECKS:
                if not check_cls.check(state, order):
                    resolutions[i] = replace(
                        resolutions[i],
                        status=Status.ILLEGAL,
                        failure_reason=check_cls.MESSAGE,
                    )
                    break
        return state.replace(resolutions=tuple(resolutions))


class MarkRedundantConvoysIllegalReducer(Reducer):
    """Mark each submitted ConvoyOrder ILLEGAL when its fleet sits on a
    longer-than-minimum chain through the same army's submitted convoys.
    Redundant convoys neither express own-nation intent nor contribute
    capacity in resolution (DATC 6.G.19, 6.F.12). Reachable-but-not-on-
    any-current-chain convoys are NOT marked here (DATC 6.G.6) —
    `is_convoy_redundant` returns False for those."""

    ACTION = Actions.MarkRedundantConvoysIllegal

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        parsed = state.parsed_orders()
        resolutions = list(state.resolutions())
        variant = state.variant()
        groups: Dict[Tuple[str, str], List[int]] = {}
        for i, order in enumerate(parsed):
            if not isinstance(order, ConvoyOrder):
                continue
            if resolutions[i].status == Status.ILLEGAL:
                continue
            source_parent = variant.parent_of(order.army_source)
            target_parent = variant.parent_of(order.army_target)
            groups.setdefault((source_parent, target_parent), []).append(i)
        for (source_parent, target_parent), indices in groups.items():
            fleet_locs = tuple(parsed[k].source for k in indices)
            for k in indices:
                if is_convoy_redundant(
                    state, parsed[k].source, source_parent, target_parent, fleet_locs
                ):
                    resolutions[k] = replace(
                        resolutions[k],
                        status=Status.ILLEGAL,
                        failure_reason="Convoy fleet is not necessary for any convoy route.",
                    )
        return state.replace(resolutions=tuple(resolutions))


class MarkConvoyedMovesReachableReducer(Reducer):
    """Decide which Army Move orders travel by convoy and reverse the
    ILLEGAL mark on Moves that are reachable only via convoy.

    Reachability case (DATC 6.D.32 vs 6.D.8): a Move flagged ILLEGAL by
    MoveTargetIsReachableCheck is un-marked when any chain of standing
    fleets in sea provinces could connect the endpoints. The resolver
    will later bounce the move if no actually-matched ConvoyOrders
    carry it.

    Intent case (DATC 6.G.1, 6.G.5): a Move that *is* directly
    reachable still becomes via_convoy when the player set
    `via_convoy` on the raw order or when an own-nation Fleet has
    issued a matching Convoy order. Marking via_convoy disables the
    head-to-head pairing for that move, enabling swap-by-convoy. A
    foreign convoy alone does not provide intent (DATC 6.G.2)."""

    ACTION = Actions.MarkConvoyedMovesReachable

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        parsed = state.parsed_orders()
        resolutions = list(state.resolutions())
        variant = state.variant()
        reach_message = MoveTargetIsReachableCheck.MESSAGE
        potential_fleet_locs = tuple(
            u.location for u in state.units().all()
            if not u.dislodged
            and u.type == Unit.FLEET
            and state.province(variant.parent_of(u.location)).is_sea()
        )
        for i, order in enumerate(parsed):
            if not isinstance(order, MoveOrder):
                continue
            if order.unit_type != Unit.ARMY:
                continue
            r = resolutions[i]
            source_parent = variant.parent_of(order.source)
            target_parent = variant.parent_of(order.target)
            if not state.province(source_parent).is_coastal():
                continue
            if not state.province(target_parent).is_coastal():
                continue
            if r.status == Status.ILLEGAL and r.failure_reason == reach_message:
                if not potential_fleet_locs:
                    continue
                if not convoy_path_exists(
                    state, source_parent, target_parent, potential_fleet_locs
                ):
                    continue
                resolutions[i] = replace(
                    r, status=None, failure_reason=None, via_convoy=True
                )
                continue
            if r.status is not None:
                continue
            if r.via_convoy:
                # Player set raw.via_convoy; already marked at parse.
                continue
            own_intent = any(
                isinstance(other, ConvoyOrder)
                and resolutions[j].status != Status.ILLEGAL
                and other.nation == order.nation
                and variant.parent_of(other.army_source) == source_parent
                and variant.parent_of(other.army_target) == target_parent
                for j, other in enumerate(parsed)
            )
            if own_intent:
                resolutions[i] = replace(r, via_convoy=True)
        return state.replace(resolutions=tuple(resolutions))


class EnforceUniqueAdjustmentTargetsReducer(Reducer):
    """For each parent province, mark all but the first still-undecided
    BuildOrder at that province ILLEGAL with a duplicate-target message;
    do the same for AdjustmentDisbandOrder independently. Iterates
    parsed_orders in submission order so 'first' means 'lowest index.'
    Builds and disbands are tracked in separate seen-sets; they don't
    conflict with each other (legality checks already enforce occupancy
    rules)."""

    ACTION = Actions.EnforceUniqueAdjustmentTargets

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        resolutions = list(state.resolutions())
        seen_build_parents: set = set()
        seen_disband_parents: set = set()
        variant = state.variant()
        for i, order in enumerate(state.parsed_orders()):
            if resolutions[i].status is not None:
                continue
            if isinstance(order, BuildOrder):
                parent = variant.parent_of(order.location)
                if parent in seen_build_parents:
                    resolutions[i] = replace(
                        resolutions[i],
                        status=Status.ILLEGAL,
                        failure_reason="Another build for this province has already been ordered.",
                    )
                else:
                    seen_build_parents.add(parent)
            elif isinstance(order, AdjustmentDisbandOrder):
                parent = variant.parent_of(order.location)
                if parent in seen_disband_parents:
                    resolutions[i] = replace(
                        resolutions[i],
                        status=Status.ILLEGAL,
                        failure_reason="This unit has already been ordered to disband.",
                    )
                else:
                    seen_disband_parents.add(parent)
        return state.replace(resolutions=tuple(resolutions))


class MatchSupportsReducer(Reducer):
    """Compute support_matched for every Support order. A Support is
    matched iff the supported unit is actually doing what the support
    claims (DATC 6.D.7, 6.D.28). ILLEGAL Supports are left as None —
    they contribute no strength regardless. The result depends only on
    parsed_orders and the ILLEGAL marks set by ApplyLegalityChecks; no
    iteration is needed."""

    ACTION = Actions.MatchSupports

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        parsed = state.parsed_orders()
        resolutions = list(state.resolutions())
        variant = state.variant()
        order_index_by_parent: Dict[str, int] = {}
        for i, order in enumerate(parsed):
            if isinstance(
                order,
                (HoldOrder, MoveOrder, SupportHoldOrder, SupportMoveOrder, ConvoyOrder),
            ):
                order_index_by_parent[variant.parent_of(order.source)] = i
        for i, order in enumerate(parsed):
            if resolutions[i].status == Status.ILLEGAL:
                continue
            if isinstance(order, SupportHoldOrder):
                supported_idx = order_index_by_parent.get(
                    variant.parent_of(order.supported_source)
                )
                if supported_idx is None:
                    resolutions[i] = replace(resolutions[i], support_matched=False)
                    continue
                supported = parsed[supported_idx]
                supported_status = resolutions[supported_idx].status
                if isinstance(supported, MoveOrder) and supported_status != Status.ILLEGAL:
                    resolutions[i] = replace(resolutions[i], support_matched=False)
                else:
                    resolutions[i] = replace(resolutions[i], support_matched=True)
            elif isinstance(order, SupportMoveOrder):
                supported_idx = order_index_by_parent.get(
                    variant.parent_of(order.supported_source)
                )
                if supported_idx is None:
                    resolutions[i] = replace(resolutions[i], support_matched=False)
                    continue
                supported = parsed[supported_idx]
                supported_status = resolutions[supported_idx].status
                if not isinstance(supported, MoveOrder) or supported_status == Status.ILLEGAL:
                    resolutions[i] = replace(resolutions[i], support_matched=False)
                # A SupportMove matches when the support's target equals the
                # move's target, or when one is the bare parent of the other.
                # Two distinct named coasts of the same parent (e.g. spa/nc
                # vs. spa/sc) do NOT match — DATC 6.B.9.
                elif (
                    order.target == supported.target
                    or order.target == variant.parent_of(supported.target)
                    or supported.target == variant.parent_of(order.target)
                ):
                    resolutions[i] = replace(resolutions[i], support_matched=True)
                else:
                    resolutions[i] = replace(resolutions[i], support_matched=False)
        return state.replace(resolutions=tuple(resolutions))


class MatchConvoysReducer(Reducer):
    """Compute convoy_matched for every Convoy order. A Convoy is
    matched iff there is a non-ILLEGAL MoveOrder from the convoy's
    army_source to its army_target (parent-province match on both).
    ILLEGAL Convoys are left as None — they contribute no convoy
    capacity regardless. The result depends only on parsed_orders and
    the ILLEGAL marks set by upstream reducers; no iteration is
    needed."""

    ACTION = Actions.MatchConvoys

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        parsed = state.parsed_orders()
        resolutions = list(state.resolutions())
        variant = state.variant()
        moves_by_endpoints: Dict[Tuple[str, str], int] = {}
        for i, order in enumerate(parsed):
            if not isinstance(order, MoveOrder):
                continue
            if resolutions[i].status == Status.ILLEGAL:
                continue
            source_parent = variant.parent_of(order.source)
            target_parent = variant.parent_of(order.target)
            moves_by_endpoints.setdefault(
                (source_parent, target_parent), i
            )
        for i, order in enumerate(parsed):
            if not isinstance(order, ConvoyOrder):
                continue
            if resolutions[i].status == Status.ILLEGAL:
                continue
            army_source = variant.parent_of(order.army_source)
            army_target = variant.parent_of(order.army_target)
            matched = (army_source, army_target) in moves_by_endpoints
            resolutions[i] = replace(resolutions[i], convoy_matched=matched)
        return state.replace(resolutions=tuple(resolutions))


class ResolveStrengthsAndCutsReducer(Reducer):
    """Resolve Movement-phase contests via the strength-and-cut solver.
    The solver itself lives in resolution.py and uses a Decision-graph
    representation appropriate to the problem; this reducer is the
    adaptor that plugs it into the action pipeline."""

    ACTION = Actions.ResolveStrengthsAndCuts

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        return resolve_strengths_and_cuts(state)


class ResolveRetreatBouncesReducer(Reducer):
    """Mark BOUNCE on every still-undecided RetreatOrder whose parent
    target is targeted by another still-undecided RetreatOrder. All
    competing retreats fail; none move (DATC 6.H.7, 6.H.8)."""

    ACTION = Actions.ResolveRetreatBounces

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        by_target = state.orders().retreats_by_target_parent()
        resolutions = list(state.resolutions())
        for parent, indices in by_target.items():
            if len(indices) < 2:
                continue
            for i in indices:
                resolutions[i] = replace(
                    resolutions[i],
                    status=Status.BOUNCE,
                    failure_reason="Multiple units retreat to the same province; all disband.",
                )
        return state.replace(resolutions=tuple(resolutions))


class EnforceBuildLimitsReducer(Reducer):
    """For each nation that submitted builds, allow at most
    `allowed_builds(state, nation)` undecided BuildOrders to remain OK.
    Excess builds in submission order are marked ILLEGAL with a
    too-many message. Orders already marked ILLEGAL by legality checks
    are skipped — they don't count against the cap."""

    ACTION = Actions.EnforceBuildLimits

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        resolutions = list(state.resolutions())
        counted: Dict[str, int] = {}
        for i, order in enumerate(state.parsed_orders()):
            if not isinstance(order, BuildOrder):
                continue
            if resolutions[i].status is not None:
                continue
            allowed = state.nation(order.nation).allowed_builds()
            used = counted.get(order.nation, 0)
            if used >= allowed:
                resolutions[i] = replace(
                    resolutions[i],
                    status=Status.ILLEGAL,
                    failure_reason="Nation has already built its allowed number of units.",
                )
            else:
                counted[order.nation] = used + 1
        return state.replace(resolutions=tuple(resolutions))


class EnforceDisbandLimitsReducer(Reducer):
    """For each nation that submitted Adjustment disbands, allow at most
    `required_disbands(state, nation)` undecided AdjustmentDisbandOrders
    to remain OK. Excess disbands in submission order are marked ILLEGAL
    with a too-many message. Orders already marked ILLEGAL by legality
    checks are skipped — they don't count against the cap."""

    ACTION = Actions.EnforceDisbandLimits

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        resolutions = list(state.resolutions())
        counted: Dict[str, int] = {}
        for i, order in enumerate(state.parsed_orders()):
            if not isinstance(order, AdjustmentDisbandOrder):
                continue
            if resolutions[i].status is not None:
                continue
            required = state.nation(order.nation).required_disbands()
            used = counted.get(order.nation, 0)
            if used >= required:
                resolutions[i] = replace(
                    resolutions[i],
                    status=Status.ILLEGAL,
                    failure_reason="Nation has already disbanded its required number of units.",
                )
            else:
                counted[order.nation] = used + 1
        return state.replace(resolutions=tuple(resolutions))


class ApplyCivilDisorderReducer(Reducer):
    """For each nation, compare the count of still-undecided
    AdjustmentDisbandOrders to the nation's required disband total. When
    short of the requirement, select additional units from the nation's
    civil-disorder ranking — skipping any already explicitly being
    disbanded — and record their locations in civil_disorder_disbands
    for ApplyAdjustmentOutcomes to remove."""

    ACTION = Actions.ApplyCivilDisorder

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        resolutions = state.resolutions()
        disbanding_by_nation: Dict[str, set] = {}
        for i, order in enumerate(state.parsed_orders()):
            if not isinstance(order, AdjustmentDisbandOrder):
                continue
            if resolutions[i].status is not None:
                continue
            disbanding_by_nation.setdefault(order.nation, set()).add(order.location)
        nations: List[str] = []
        for u in state.units().all():
            if u.dislodged:
                continue
            if u.nation not in nations:
                nations.append(u.nation)
        civil: List[str] = []
        for nation in nations:
            nation_view = state.nation(nation)
            required = nation_view.required_disbands()
            already = disbanding_by_nation.get(nation, set())
            shortfall = required - len(already)
            if shortfall <= 0:
                continue
            picked = 0
            for unit in nation_view.civil_disorder_ranking():
                if picked >= shortfall:
                    break
                if unit.location in already:
                    continue
                civil.append(unit.location)
                picked += 1
        return state.replace(civil_disorder_disbands=tuple(sorted(civil)))


class FinalizeStatusesReducer(Reducer):
    """Promote any order whose status is still None to its final value.
    Support orders read their final status from support_matched plus
    support_cut: an unmatched support reports ILLEGAL (the supportee was
    not ordered to perform the supported action, matching godip's
    ErrInvalidSupporteeOrder), a matched support reports the resolved
    support_cut value. Convoy orders whose convoying fleet was dislodged
    by a successful attack report BOUNCE with a disruption reason
    (matches godip's ErrConvoyDislodged). All other still-undecided
    orders become OK. After this runs, every entry in order_status is one
    of Status.{OK,ILLEGAL,BOUNCE,CUT}."""

    ACTION = Actions.FinalizeStatuses

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        parsed = state.parsed_orders()
        resolutions = list(state.resolutions())
        for i, order in enumerate(parsed):
            r = resolutions[i]
            if r.status is not None:
                continue
            if isinstance(order, (SupportHoldOrder, SupportMoveOrder)):
                if r.support_matched:
                    resolutions[i] = replace(r, status=r.support_cut or Status.OK)
                else:
                    resolutions[i] = replace(
                        r,
                        status=Status.ILLEGAL,
                        failure_reason="The supported unit was not ordered to perform the supported action.",
                    )
                continue
            if isinstance(order, ConvoyOrder) and cls._convoy_fleet_dislodged(
                state, order
            ):
                resolutions[i] = replace(
                    r,
                    status=Status.BOUNCE,
                    failure_reason="The convoying fleet was dislodged.",
                )
                continue
            resolutions[i] = replace(r, status=Status.OK)
        return state.replace(resolutions=tuple(resolutions))

    @classmethod
    def _convoy_fleet_dislodged(
        cls, state: StateView, order: ConvoyOrder
    ) -> bool:
        variant = state.variant()
        fleet_parent = variant.parent_of(order.source)
        resolutions = state.resolutions()
        for j, other in enumerate(state.parsed_orders()):
            if not isinstance(other, MoveOrder):
                continue
            if resolutions[j].status != Status.OK:
                continue
            if variant.parent_of(other.target) != fleet_parent:
                continue
            return True
        return False


class ApplyMovementOutcomesReducer(Reducer):
    """Compute the Movement-phase post-resolution units list and the set
    of contested parent provinces. Units whose Move resolved OK relocate
    to the move's target. Units whose location is the target parent of
    another unit's successful Move become dislodged, with dislodged_from
    set to the parent of the attacker's source — except when the attacker
    is the same nation as the defender, in which case the strength-based
    resolver already bounced the move and no dislodgement occurs. All
    other standing units pass through unchanged. The contested-provinces
    output collects every parent province where two or more non-ILLEGAL
    Moves competed and none succeeded (a stand-off per DATC 6.H.6).
    Finally, any dislodged unit with no legal retreat target is removed
    from next_units — a unit that could not retreat during the following
    Retreat phase is disbanded as the Movement phase resolves rather
    than carried forward."""

    ACTION = Actions.ApplyMovementOutcomes

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        state = cls._compute_next_units(state)
        state = cls._compute_next_contested_provinces(state)
        state = cls._drop_dislodged_units_with_no_retreat(state)
        return state

    @classmethod
    def _compute_next_units(cls, state: StateView) -> StateView:
        """Produce the post-Movement units list. Units whose Move
        resolved OK relocate; units whose location is the target parent
        of another unit's successful Move become dislodged (with
        dislodged_from set to the attacker's source parent, except when
        the attacker arrived via convoy — DATC's convoy retreat
        exception: a convoyed attacker leaves no attacker-origin
        restriction on the dislodged unit's retreat); all other units
        pass through unchanged. Head-to-head winners relocate as
        usual; their h2h opponents bounce and are dislodged by the
        winner's move just like any other defender. Same-nation
        dislodgement cannot occur here because the resolver already
        bounces such attacks."""
        parsed = state.parsed_orders()
        resolutions = state.resolutions()
        variant = state.variant()
        moves_out: Dict[str, str] = {}
        attackers_by_parent: Dict[str, Tuple[str, bool]] = {}
        for i, order in enumerate(parsed):
            if not isinstance(order, MoveOrder):
                continue
            if resolutions[i].status != Status.OK:
                continue
            moves_out[order.source] = order.target
            attackers_by_parent.setdefault(
                variant.parent_of(order.target),
                (order.source, resolutions[i].via_convoy),
            )
        next_units: List[Unit] = []
        for unit in state.units().all():
            if unit.dislodged:
                next_units.append(unit)
                continue
            if unit.location in moves_out:
                next_units.append(
                    replace(
                        unit,
                        location=moves_out[unit.location],
                        dislodged=False,
                        dislodged_from=None,
                    )
                )
                continue
            attacker = attackers_by_parent.get(variant.parent_of(unit.location))
            if attacker is not None:
                attacker_source, attacker_via_convoy = attacker
                next_units.append(
                    replace(
                        unit,
                        dislodged=True,
                        dislodged_from=(
                            None
                            if attacker_via_convoy
                            else variant.parent_of(attacker_source)
                        ),
                    )
                )
                continue
            next_units.append(unit)
        return state.replace(next_units=tuple(next_units))

    @classmethod
    def _compute_next_contested_provinces(cls, state: StateView) -> StateView:
        """Collect every parent province that was the site of a stand-off:
        two or more non-ILLEGAL Moves targeted it and none succeeded.
        Provinces where one Move succeeded (the attacker entered) are not
        contested — the new occupant blocks retreats anyway. The result
        carries into the next phase's State.contested_provinces and is
        consulted by RetreatTargetIsNotContestedCheck (DATC 6.H.6)."""
        parsed = state.parsed_orders()
        resolutions = state.resolutions()
        variant = state.variant()
        by_target: Dict[str, List[int]] = {}
        for i, order in enumerate(parsed):
            if not isinstance(order, MoveOrder):
                continue
            if resolutions[i].status == Status.ILLEGAL:
                continue
            by_target.setdefault(variant.parent_of(order.target), []).append(i)
        contested: List[str] = []
        for parent, indices in by_target.items():
            if len(indices) < 2:
                continue
            if any(resolutions[i].status == Status.OK for i in indices):
                continue
            contested.append(parent)
        return state.replace(next_contested_provinces=tuple(sorted(contested)))

    @classmethod
    def _drop_dislodged_units_with_no_retreat(cls, state: StateView) -> StateView:
        """Remove from next_units any dislodged unit that has no legal
        retreat target. A unit that would enter the following Retreat
        phase with zero retreat options is disbanded as the Movement
        phase resolves — godip applies this same rule in its Movement
        post-processing. Retreat-legality is reused from
        RetreatOrder.LEGALITY_CHECKS, evaluated against a state-view
        whose units list is the post-Movement next_units and whose
        contested_provinces is the standoff set produced by
        _compute_next_contested_provinces — i.e. the world as the
        Retreat phase would see it."""
        next_units = state.next_units()
        if not any(u.dislodged for u in next_units):
            return state
        post_movement = state.replace(
            units=next_units,
            contested_provinces=state.next_contested_provinces(),
        )
        variant = state.variant()
        candidate_targets = tuple(variant.provinces.keys()) + tuple(
            variant.named_coasts.keys()
        )
        kept: List[Unit] = []
        for unit in next_units:
            if not unit.dislodged:
                kept.append(unit)
                continue
            has_retreat = False
            for target in candidate_targets:
                order = RetreatOrder(
                    nation=unit.nation,
                    source=unit.location,
                    target=target,
                    unit_type=unit.type,
                    dislodged_from=unit.dislodged_from,
                )
                if all(
                    c.check(post_movement, order)
                    for c in RetreatOrder.LEGALITY_CHECKS
                ):
                    has_retreat = True
                    break
            if has_retreat:
                kept.append(unit)
        return state.replace(next_units=tuple(kept))


class ApplyRetreatOutcomesReducer(Reducer):
    """Keep non-dislodged units in place (dislodged flag cleared). For
    each dislodged unit, look up its parsed order: a successful retreat
    moves the unit to its target; anything else (disband, illegal,
    bounce) removes the unit from the board."""

    ACTION = Actions.ApplyRetreatOutcomes

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        next_units: List[Unit] = []
        orders_by_source = state.orders().by_source()
        resolutions = state.resolutions()
        for unit in state.units().all():
            if not unit.dislodged:
                next_units.append(unit)
                continue
            index_order = orders_by_source.get(unit.location)
            if index_order is None:
                continue
            index, order = index_order
            if isinstance(order, RetreatOrder) and resolutions[index].status == Status.OK:
                next_units.append(
                    replace(
                        unit,
                        location=order.target,
                        dislodged=False,
                        dislodged_from=None,
                    )
                )
        return state.replace(next_units=tuple(next_units))


class UpdateSupplyCenterOwnershipReducer(Reducer):
    """Recompute supply-center ownership for the next phase. When the
    next phase is an Adjustment phase, ownership is recounted from the
    post-retreat unit positions (next_units): every supply-center
    province occupied by a unit transfers to that unit's nation, and
    unoccupied supply centers keep their current owner. When the next
    phase is not an Adjustment phase, current ownership is carried
    through unchanged. Writes next_supply_centers."""

    ACTION = Actions.UpdateSupplyCenterOwnership

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        next_phase = state.next_phase()
        if next_phase is None or next_phase.type != Phase.ADJUSTMENT:
            return state.replace(next_supply_centers=state.supply_centers())
        variant = state.variant()
        occupant_by_province: Dict[str, str] = {}
        for unit in state.next_units():
            occupant_by_province[variant.parent_of(unit.location)] = unit.nation
        current_by_province = {sc.province: sc for sc in state.supply_centers()}
        updated: List[SupplyCenter] = []
        for province_id, province in sorted(variant.provinces.items()):
            if not province.supply_center:
                continue
            occupant = occupant_by_province.get(province_id)
            current = current_by_province.get(province_id)
            if occupant is None:
                if current is not None:
                    updated.append(current)
            elif current is None:
                updated.append(SupplyCenter(nation=occupant, province=province_id))
            elif current.nation == occupant:
                updated.append(current)
            else:
                updated.append(replace(current, nation=occupant))
        return state.replace(next_supply_centers=tuple(updated))


class ApplyAdjustmentOutcomesReducer(Reducer):
    """Compute the Adjustment-phase post-resolution units list. First,
    drop units removed this phase — both those explicitly disbanded by
    OK AdjustmentDisbandOrders and those selected for civil-disorder
    disband. Then, append a new unit for each OK BuildOrder. The
    Adjustment phase does not see dislodged units — they were handled
    in the prior Retreat phase."""

    ACTION = Actions.ApplyAdjustmentOutcomes

    @classmethod
    def reduce(cls, state: StateView, action: Action) -> StateView:
        state = cls._remove_disbanded_units(state)
        state = cls._append_built_units(state)
        return state

    @classmethod
    def _remove_disbanded_units(cls, state: StateView) -> StateView:
        """Populate next_units with the non-dislodged units whose location
        is not the source of an OK AdjustmentDisbandOrder and not in the
        civil-disorder set."""
        disbanded: set = set(state.civil_disorder_disbands())
        resolutions = state.resolutions()
        for i, order in enumerate(state.parsed_orders()):
            if not isinstance(order, AdjustmentDisbandOrder):
                continue
            if resolutions[i].status != Status.OK:
                continue
            disbanded.add(order.location)
        kept = tuple(
            u for u in state.units().all()
            if not u.dislodged and u.location not in disbanded
        )
        return state.replace(next_units=kept)

    @classmethod
    def _append_built_units(cls, state: StateView) -> StateView:
        """Append a new Unit for each OK BuildOrder onto next_units."""
        next_units: List[Unit] = list(state.next_units())
        resolutions = state.resolutions()
        for i, order in enumerate(state.parsed_orders()):
            if not isinstance(order, BuildOrder):
                continue
            if resolutions[i].status != Status.OK:
                continue
            next_units.append(
                Unit(
                    nation=order.nation,
                    type=order.unit_type or Unit.ARMY,
                    location=order.location,
                )
            )
        return state.replace(next_units=tuple(next_units))


# === Phase resolvers ===


_PHASE_RESOLVER_REGISTRY: Dict[str, Type["PhaseResolver"]] = {}


class PhaseResolver:
    """Base class for phase-resolver classes. Each subclass is paired
    with exactly one phase type via the PHASE_TYPE class attribute
    (Phase.MOVEMENT / Phase.RETREAT / Phase.ADJUSTMENT) and declares
    an ACTIONS tuple of Action classes; actions_for(state) instantiates
    them in order for the Engine's dispatch loop.

    Subclasses are auto-registered into the phase-resolver registry
    when the class body is evaluated, via __init_subclass__. There is
    no need to decorate subclasses — declaring the PHASE_TYPE attribute
    is enough.

    Subclasses override actions_for only if they need conditional
    pipelines or actions requiring state-derived payloads.
    """

    PHASE_TYPE: ClassVar[str]
    ACTIONS: ClassVar[Tuple[Type[Action], ...]] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PHASE_TYPE"):
            _PHASE_RESOLVER_REGISTRY[cls.PHASE_TYPE] = cls

    @classmethod
    def actions_for(cls, state: AdjudicationState) -> List[Action]:
        """Materialise each entry in ACTIONS by constructing it with no
        args. Phase resolvers with branching pipelines or actions
        requiring data payloads override this directly to construct
        actions explicitly."""
        return [action_cls() for action_cls in cls.ACTIONS]


class MovementPhaseResolver(PhaseResolver):
    """Movement-phase pipeline:
      1. ParseMovementOrders        — assign each unit a Hold, Move,
                                      Support, or Convoy order
                                      (default Hold).
      2. ApplyLegalityChecks        — per-order LEGALITY_CHECKS, including
                                      reachability for Moves and the
                                      support-existence / reach / self
                                      checks for Supports. Coastal-to-
                                      coastal Moves needing a convoy
                                      fail reachability here and are
                                      revisited in step 3.
      3. MarkConvoyedMovesReachable — un-mark MoveOrders flagged ILLEGAL
                                      by reachability when a static
                                      convoy path exists through the
                                      submitted non-ILLEGAL ConvoyOrders.
      4. MatchSupports              — decide which non-ILLEGAL Supports
                                      actually attach to the supported
                                      unit's behavior.
      5. MatchConvoys               — decide which non-ILLEGAL Convoys
                                      have a corresponding non-ILLEGAL
                                      Move from army_source to
                                      army_target. Writes convoy_matched.
      6. ResolveStrengthsAndCuts    — dependency-tracked Decision-graph
                                      resolution of support cuts, attack /
                                      defense / prevent / hold strengths,
                                      and Move statuses (including head-to-
                                      head and self-dislodgement). The
                                      solver itself lives in resolution.py.
      7. FinalizeStatuses           — remaining undecided -> OK; Supports
                                      mirror Status from support_cut.
      8. ApplyMovementOutcomes      — relocate successful Moves, mark
                                      dislodged units (skipping same-
                                      nation dislodgement), record
                                      contested provinces."""

    PHASE_TYPE = Phase.MOVEMENT

    ACTIONS = (
        Actions.ParseMovementOrders,
        Actions.ApplyLegalityChecks,
        Actions.MarkRedundantConvoysIllegal,
        Actions.MarkConvoyedMovesReachable,
        Actions.MatchSupports,
        Actions.MatchConvoys,
        Actions.ResolveStrengthsAndCuts,
        Actions.FinalizeStatuses,
        Actions.ApplyMovementOutcomes,
    )


class RetreatPhaseResolver(PhaseResolver):
    """Retreat-phase pipeline:
    1. ParseRetreatOrders      — assign retreat / disband per dislodged unit.
    2. ApplyLegalityChecks     — reachable / unoccupied / not-attacker / not-contested.
    3. ResolveRetreatBounces   — standoffs mark all competitors BOUNCE.
    4. FinalizeStatuses        — remaining undecided -> OK.
    5. ApplyRetreatOutcomes    — relocate or remove dislodged units.
    6. UpdateSupplyCenterOwnership
                               — recompute supply-center ownership from
                                 the post-retreat positions when the next
                                 phase is Adjustment; carry it through
                                 unchanged otherwise."""

    PHASE_TYPE = Phase.RETREAT

    ACTIONS = (
        Actions.ParseRetreatOrders,
        Actions.ApplyLegalityChecks,
        Actions.ResolveRetreatBounces,
        Actions.FinalizeStatuses,
        Actions.ApplyRetreatOutcomes,
        Actions.UpdateSupplyCenterOwnership,
    )


class AdjustmentPhaseResolver(PhaseResolver):
    """Adjustment-phase pipeline:
    1. ParseAdjustmentOrders   — wrap each Build/Disband raw order, dropping
                                 Disbands with no matching standing unit.
    2. ApplyLegalityChecks     — full build-legality + disband-legality
                                 check lists.
    3. EnforceUniqueAdjustmentTargets
                               — first-wins disambiguation: only the first
                                 still-undecided Build (and, separately, the
                                 first Disband) per parent province survives;
                                 later duplicates are marked ILLEGAL.
    4. EnforceBuildLimits      — cap successful builds at allowed per nation.
    5. EnforceDisbandLimits    — cap successful disbands at required per nation.
    6. ApplyCivilDisorder      — fill any disband shortfall via the ranked
                                 civil-disorder selection.
    7. FinalizeStatuses        — remaining undecided -> OK.
    8. ApplyAdjustmentOutcomes — drop disbanded units (explicit + civil),
                                 then append new units for OK builds."""

    PHASE_TYPE = Phase.ADJUSTMENT

    ACTIONS = (
        Actions.ParseAdjustmentOrders,
        Actions.ApplyLegalityChecks,
        Actions.EnforceUniqueAdjustmentTargets,
        Actions.EnforceBuildLimits,
        Actions.EnforceDisbandLimits,
        Actions.ApplyCivilDisorder,
        Actions.FinalizeStatuses,
        Actions.ApplyAdjustmentOutcomes,
    )


# === Engine ===


class Engine:
    """Public entry point for the prototype adjudicator. Holds the reducer
    and phase-resolver registries (both populated at import time via
    __init_subclass__ on the respective base classes) and exposes
    adjudicate(state) -> List[State].

    The engine converts the external State (mutable dataclass tree from
    .domain) into a frozen AdjudicationState, dispatches each action
    listed by the phase resolver against it, and converts the result
    back into one or two external States — the resolved input phase and
    optionally a fresh next-phase state. Phase skipping, solo-victory
    detection, and get_options are out of scope for the prototype."""

    def adjudicate(self, state: State) -> List[State]:
        """Resolve a single phase. Returns [resolved] when state.phase has
        no successor, otherwise [resolved, next_state]. Raises
        NotImplementedError when state.phase.type is not one of
        MOVEMENT / RETREAT / ADJUSTMENT — or when the slice doesn't
        cover an order type present in state.orders (raised by the
        parse_* reducer of the relevant phase)."""
        resolver_cls = _PHASE_RESOLVER_REGISTRY.get(state.phase.type)
        if resolver_cls is None:
            raise NotImplementedError(
                f"Phase type {state.phase.type!r} is outside the prototype slice."
            )
        adj = self._to_adjudication_state(state)
        for action in resolver_cls.actions_for(adj):
            adj = self.dispatch(adj, action)
        return self._to_external_states(state, adj)

    def dispatch(self, state: AdjudicationState, action: Action) -> AdjudicationState:
        """Look up the Reducer subclass registered for `type(action)` and
        apply its `reduce` classmethod. Wraps state into a StateView for
        the reducer and unwraps the returned view via .raw. Raises
        ValueError if no reducer is registered — that indicates a wiring
        bug, not a user-input problem."""
        reducer = _REDUCER_REGISTRY.get(type(action))
        if reducer is None:
            raise ValueError(f"No reducer registered for {type(action).__name__}")
        view = StateView(state)
        result = reducer.reduce(view, action)
        return result.raw

    def _to_adjudication_state(self, state: State) -> AdjudicationState:
        """Freeze the external State into an AdjudicationState. Mutable
        sequences from State become tuples; resolution-output fields
        start empty."""
        return AdjudicationState(
            variant=state.variant,
            phase=state.phase,
            units=tuple(state.units),
            supply_centers=tuple(state.supply_centers),
            raw_orders=tuple(state.orders),
            contested_provinces=tuple(state.contested_provinces),
        )

    def _to_external_states(
        self, original: State, adj: AdjudicationState
    ) -> List[State]:
        """Build the resolved State from `adj` (resolutions populated,
        units replaced with next_units) and, if applicable, a fresh
        next-phase State carrying those units forward. The next-phase
        State takes its supply-center ownership from next_supply_centers
        when a reducer recomputed it (Retreat phase), otherwise the
        input ownership is carried through unchanged."""
        resolutions: List[Resolution] = []
        for order, resolution in zip(adj.parsed_orders, adj.resolutions):
            resolutions.append(
                Resolution(
                    province=order.source_province(),
                    resolution=resolution.status or Status.OK,
                    reason=resolution.failure_reason,
                )
            )
        for location in adj.civil_disorder_disbands:
            resolutions.append(
                Resolution(
                    province=location,
                    resolution=Status.OK,
                    reason="Disbanded due to civil disorder.",
                )
            )
        resolved = State(
            variant=original.variant,
            phase=original.phase,
            units=list(adj.next_units),
            supply_centers=list(original.supply_centers),
            orders=list(original.orders),
            resolutions=resolutions,
            skipped=False,
            outcome=None,
            contested_provinces=tuple(original.contested_provinces),
        )
        nxt = StateView(adj).next_phase()
        if nxt is None:
            return [resolved]
        next_state = State(
            variant=original.variant,
            phase=nxt,
            units=list(adj.next_units),
            supply_centers=list(adj.next_supply_centers or original.supply_centers),
            orders=[],
            resolutions=None,
            skipped=False,
            outcome=None,
            contested_provinces=tuple(adj.next_contested_provinces),
        )
        return [resolved, next_state]
