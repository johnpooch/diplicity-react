"""Shared types for the adjudicator: orders, checks, state, and views.

Lives in its own module because both `engine.py` (the orchestration
layer) and `resolution.py` (the strength solver) need to construct,
inspect, and type-check these values. Putting them here breaks the
otherwise-circular import between those two modules.

The rubric's eight-category model applies to this module: every class
here belongs to exactly one of Order, Check, State, or View. No
behavior beyond the trivial identity accessor `source_province` on
Order subclasses.
"""
from __future__ import annotations

# === Imports ===
from dataclasses import dataclass, replace
from typing import ClassVar, Dict, List, Optional, Tuple, Type

from .domain import (
    Order as RawOrder,
)
from .domain import (
    Phase,
    PhaseTransition,
    ProvinceType,
    SupplyCenter,
    Unit,
    Variant,
)

# === Status constants ===


class Status:
    """Resolution values written into OrderResolution.status (on each entry
    of AdjudicationState.resolutions) and propagated to the external
    Resolution records. Mirrors the existing engine's ResolutionType
    (OK / BOUNCE / ILLEGAL / CUT)."""

    OK: ClassVar[str] = "OK"
    ILLEGAL: ClassVar[str] = "ILLEGAL"
    BOUNCE: ClassVar[str] = "BOUNCE"
    CUT: ClassVar[str] = "CUT"


class OrderType:
    """Wire-format order-type ids accepted in the prototype slice. Any
    raw order whose `order_type` is not one of these raises
    NotImplementedError at parse time."""

    HOLD: ClassVar[str] = "Hold"
    MOVE: ClassVar[str] = "Move"
    SUPPORT: ClassVar[str] = "Support"
    CONVOY: ClassVar[str] = "Convoy"
    RETREAT: ClassVar[str] = "Retreat"
    DISBAND: ClassVar[str] = "Disband"
    BUILD: ClassVar[str] = "Build"


# Variant modifier id permitting builds in any owned supply center.
ALLOW_NON_HOME_BUILDS: str = "allow-builds-in-non-home-centers"


# === Marker base classes ===


class Order:
    """Empty marker base for concrete Order dataclasses. Exists so the
    type system can express `Tuple[Order, ...]` and so reducers / selectors
    can isinstance-check across all order types. No behavior beyond the
    trivial identity accessor `source_province`."""

    def source_province(self) -> str:
        """Return the parent province (or named coast) this order pertains
        to. The field name varies across subclasses — `source` for
        movement-phase orders, `location` for adjustment-phase orders —
        and this accessor is the uniform interface for consumers that
        don't need to know which kind of order they're holding."""
        raise NotImplementedError


class Action:
    """Empty marker base for the inner classes of the `Actions` namespace.
    Exists for typing and isinstance — actions carry only the data needed
    to perform a transition; the reducer holds all logic."""


class Check:
    """Stateless predicate over (StateView, Order). Subclasses declare
    the MESSAGE shown to players when the check fails and a classmethod
    `check` returning True iff the order satisfies the rule.

    Composed into Order subclasses via the LEGALITY_CHECKS class attribute
    and applied by the `ApplyLegalityChecks` reducer. Checks are pure
    predicates over the *input* state — they may not depend on the
    resolutions of other orders in the same phase. First-wins
    disambiguation (e.g. only one build per parent province per phase) is
    handled by separate enforcement reducers downstream of
    ApplyLegalityChecks, not by Checks reading interim state.
    """

    MESSAGE: ClassVar[str] = ""

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        """Return True iff `order` satisfies this rule. Subclasses override."""
        raise NotImplementedError


# === Check classes ===

# Movement-phase checks (DATC 6.A). Declared before Order classes so
# MoveOrder.LEGALITY_CHECKS can reference the class objects directly.
# Convoy-induced reachability is out of scope for the prototype slice;
# MoveTargetIsReachableCheck rejects any non-adjacent target.


class MoveTargetIsNotSourceCheck(Check):
    """A Move's target must differ from the unit's source location
    (a unit can't move to itself)."""

    MESSAGE = "A unit can't move to its own location."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, MoveOrder)
        return order.target != order.source


class MoveTargetIsReachableCheck(Check):
    """A Move's target must be adjacent to the source for the unit's
    pass type, using the variant's adjacency graph. Convoyed moves are
    outside the prototype slice — non-adjacent targets are illegal."""

    MESSAGE = "The unit can't reach the target province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, MoveOrder)
        return state.variant().can_move(order.source, order.target, order.unit_type)


# Support-order checks (DATC 6.A.13, 6.D.5–6.D.8). Declared before Order
# classes so SupportHoldOrder.LEGALITY_CHECKS / SupportMoveOrder.LEGALITY_CHECKS
# can reference the class objects directly.


class SupportHoldNotSelfSupportCheck(Check):
    """A unit can't support a unit at its own province (DATC 6.D.7).
    Parent-province comparison handles named coasts."""

    MESSAGE = "A unit can't support itself."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportHoldOrder)
        parent_of = state.variant().parent_of
        return parent_of(order.supported_source) != parent_of(order.source)


class SupportHoldHasSupportedUnitCheck(Check):
    """A SupportHold requires a standing unit at the supported province
    (parent-province match accepted)."""

    MESSAGE = "There's no unit at the supported province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportHoldOrder)
        return state.units().at_parent(order.supported_source) is not None


class SupportHoldSupporterCanReachCheck(Check):
    """The supporter must be able to support to the supported province
    using the variant's adjacency graph for its unit type
    (DATC 6.A.13)."""

    MESSAGE = "The supporting unit can't reach the supported province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportHoldOrder)
        return state.variant().can_support_to(
            order.source, order.supported_source, order.unit_type
        )


class SupportMoveNotIntoSelfCheck(Check):
    """A unit can't support an attack into its own province (DATC 6.D.6).
    Parent-province comparison handles named coasts."""

    MESSAGE = "A unit can't support an attack into its own province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportMoveOrder)
        parent_of = state.variant().parent_of
        return parent_of(order.target) != parent_of(order.source)


class SupportMoveHasSupportedUnitCheck(Check):
    """A SupportMove requires a standing unit at the supported-source
    province (parent-province match accepted)."""

    MESSAGE = "There's no unit at the supported source province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportMoveOrder)
        return state.units().at_parent(order.supported_source) is not None


class SupportMoveSupporterCanReachCheck(Check):
    """The supporter must be able to support to the target province using
    the variant's adjacency graph for its unit type (DATC 6.A.13)."""

    MESSAGE = "The supporting unit can't reach the target."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportMoveOrder)
        return state.variant().can_support_to(
            order.source, order.target, order.unit_type
        )


class SupportMoveSupportedCanReachCheck(Check):
    """The supported unit must itself be able to reach the target. For
    an army between coastal provinces, this is satisfied when a chain
    of submitted ConvoyOrders (matching the army's source and target)
    forms a sea-province path through standing fleets (DATC 6.F.3).
    Without a submitted convoy, an army's non-adjacent support target
    is illegal even when fleets that *could* have convoyed are present
    on the board (DATC 6.D.31). Without a standing unit at the
    supported source the check passes — SupportMoveHasSupportedUnitCheck
    will reject that case first."""

    MESSAGE = "The supported unit can't itself reach the target."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, SupportMoveOrder)
        supported = state.units().at_parent(order.supported_source)
        if supported is None:
            return True
        variant = state.variant()
        if variant.can_support_to(supported.location, order.target, supported.type):
            return True
        if supported.type != Unit.ARMY:
            return False
        source_parent = variant.parent_of(supported.location)
        target_parent = variant.parent_of(order.target)
        if not state.province(source_parent).is_coastal():
            return False
        if not state.province(target_parent).is_coastal():
            return False
        # Only fleets that have actually submitted a matching Convoy
        # order count — physical possibility alone is not enough
        # (DATC 6.D.31).
        convoy_fleet_locs = tuple(
            o.source
            for o in state.parsed_orders()
            if isinstance(o, ConvoyOrder)
            and variant.parent_of(o.army_source) == source_parent
            and variant.parent_of(o.army_target) == target_parent
        )
        if not convoy_fleet_locs:
            return False
        from .convoy import convoy_path_exists
        return convoy_path_exists(
            state, source_parent, target_parent, convoy_fleet_locs
        )


# Convoy-order checks (DATC 6.F, 6.G). Declared before Order classes so
# ConvoyOrder.LEGALITY_CHECKS can reference the class objects directly.
# Convoy matching, path-finding, and disruption integration into move
# resolution are out of scope for C1 — these checks cover only the
# static legality of the ConvoyOrder itself.


class ConvoyerIsFleetCheck(Check):
    """A ConvoyOrder may only be issued by a fleet."""

    MESSAGE = "Only fleets can convoy."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        return order.unit_type == Unit.FLEET


class ConvoyerIsInSeaCheck(Check):
    """The convoying fleet must be in a sea province. Named coasts are
    not sea provinces; a fleet at STP/NC cannot convoy. The variant's
    province type distinguishes sea from coastal."""

    MESSAGE = "A convoying fleet must be in a sea province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        if order.source in state.variant().named_coasts:
            return False
        return state.province(state.variant().parent_of(order.source)).is_sea()


class ConvoyArmyExistsCheck(Check):
    """There must be a standing unit at the convoy source province.
    Parent-province match accepted so that convoy orders referencing
    the army's parent province work even when units carry named-coast
    locations."""

    MESSAGE = "There's no army at the convoy source province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        return state.units().at_parent(order.army_source) is not None


class ConvoyArmyIsArmyCheck(Check):
    """The unit at the convoy source province must be an Army. Convoying
    a fleet is meaningless. Vacuously true if no unit exists at the
    source — `ConvoyArmyExistsCheck` will reject that case first."""

    MESSAGE = "Convoyed unit must be an army."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        army = state.units().at_parent(order.army_source)
        if army is None:
            return True
        return army.type == Unit.ARMY


class ConvoyEndpointsAreCoastalCheck(Check):
    """Both `army_source` and `army_target` must be coastal provinces.
    Armies can only embark from and disembark to coastal land — sea
    provinces and inland provinces cannot be convoy endpoints."""

    MESSAGE = "Convoy endpoints must be coastal provinces."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        variant = state.variant()
        return (
            state.province(variant.parent_of(order.army_source)).is_coastal()
            and state.province(variant.parent_of(order.army_target)).is_coastal()
        )


class ConvoyEndpointsDifferCheck(Check):
    """A convoy from a province to itself is meaningless."""

    MESSAGE = "Convoy source and target must differ."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        return order.army_source != order.army_target


class ConvoyFleetReachesEndpointsCheck(Check):
    """The convoying fleet must be topologically capable of reaching both
    convoy endpoints through a chain of sea provinces (DATC 6.G.7). A
    fleet that physically cannot participate in any convoy chain for
    these endpoints — e.g. Gulf of Bothnia attempting to convoy an army
    from Sweden to Norway — is rejected. Submitted-but-impossible
    convoy orders provide no own-nation intent for adjacent moves."""

    MESSAGE = "Convoy fleet is not necessary for any convoy route."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, ConvoyOrder)
        from .convoy import fleet_reaches_coast
        variant = state.variant()
        source = variant.parent_of(order.army_source)
        target = variant.parent_of(order.army_target)
        return (
            fleet_reaches_coast(state, order.source, source)
            and fleet_reaches_coast(state, order.source, target)
        )


# Retreat-phase checks (DATC 6.H.X.). Declared before Order classes so
# RetreatOrder.LEGALITY_CHECKS can reference the class objects directly.


class RetreatTargetIsReachableCheck(Check):
    """The retreat target must be adjacent to the dislodged unit's location,
    using the variant's adjacency graph and respecting the unit's pass type
    (DATC 6.H.1)."""

    MESSAGE = "The unit can't reach the retreat destination."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, RetreatOrder)
        return state.variant().can_move(order.source, order.target, order.unit_type)


class RetreatTargetIsUnoccupiedCheck(Check):
    """The retreat target's parent province must be empty of any standing
    (non-dislodged) unit (DATC 6.H.2)."""

    MESSAGE = "There is already a unit at the retreat destination."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, RetreatOrder)
        target_parent = state.variant().parent_of(order.target)
        for loc in state.units().standing_by_loc():
            if state.variant().parent_of(loc) == target_parent:
                return False
        return True


class RetreatNotToAttackerOriginCheck(Check):
    """A dislodged unit may not retreat to the parent province of the
    attacker that dislodged it (DATC 6.H.3). When the attacker came by
    convoy the original engine stores `dislodged_from=None` and this
    check vacuously passes."""

    MESSAGE = "A unit can't retreat to the province its attacker came from."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, RetreatOrder)
        if order.dislodged_from is None:
            return True
        return state.variant().parent_of(order.target) != state.variant().parent_of(
            order.dislodged_from
        )


class RetreatTargetIsNotContestedCheck(Check):
    """A retreat may not target a parent province that was contested by a
    standoff during the preceding Movement phase (DATC 6.H.6). The
    contested set lives on `state.contested_provinces`."""

    MESSAGE = "The retreat destination is contested."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, RetreatOrder)
        return (
            state.variant().parent_of(order.target) not in state.contested_provinces()
        )


# Adjustment-phase build checks. Each is a single named rule; together
# they cover the legality criteria of DATC 6.I plus the variant-modifier
# extension allowing builds in any owned supply center.


class BuildUnitTypeIsValidCheck(Check):
    """The wire-format unit type must be Army or Fleet."""

    MESSAGE = "Build order has an invalid unit type."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        return order.unit_type in (Unit.ARMY, Unit.FLEET)


class BuildLocationIsSupplyCenterCheck(Check):
    """The build location's parent province must be a supply center known
    to the variant (DATC 6.I.1)."""

    MESSAGE = "Build location is not a supply center."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        variant = state.variant()
        if (
            order.location not in variant.provinces
            and order.location not in variant.named_coasts
        ):
            return False
        parent = variant.parent_of(order.location)
        province = variant.provinces.get(parent)
        return province is not None and province.supply_center


class BuildLocationIsOwnedCheck(Check):
    """The build location's parent supply center must be currently owned
    by the building nation (DATC 6.I.1)."""

    MESSAGE = "Build location is not owned by this nation."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        parent = state.variant().parent_of(order.location)
        return parent in state.nation(order.nation).owned_supply_centers()


class BuildLocationIsHomeCenterCheck(Check):
    """The build location's parent supply center must be a home center of
    the building nation, unless the variant declares the
    `allow-builds-in-non-home-centers` adjudication modifier."""

    MESSAGE = "Build location is not a home supply center for this nation."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        if ALLOW_NON_HOME_BUILDS in state.variant().adjudication_modifiers:
            return True
        parent = state.variant().parent_of(order.location)
        province = state.variant().provinces.get(parent)
        return province is not None and province.home_nation == order.nation


class BuildArmyNotAtNamedCoastCheck(Check):
    """An army may not be built at a named coast; the location must be a
    parent province id."""

    MESSAGE = "An army cannot be built at a named coast."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        if order.unit_type != Unit.ARMY:
            return True
        return order.location not in state.variant().named_coasts


class BuildFleetCoastIsSpecifiedCheck(Check):
    """A fleet built at a multi-coast parent province must name which
    coast it occupies; building at the bare parent id is ambiguous."""

    MESSAGE = "A fleet build in a multi-coast province must specify a named coast."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        if order.unit_type != Unit.FLEET:
            return True
        parent = state.variant().parent_of(order.location)
        if order.location != parent:
            return True
        return not state.variant().coasts_of(parent)


class BuildFleetLocationIsCoastalCheck(Check):
    """A fleet must be built at a coastal location: a named coast, or a
    parent province with at least one fleet-passable adjacency."""

    MESSAGE = "A fleet cannot be built in a landlocked province."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        if order.unit_type != Unit.FLEET:
            return True
        if order.location in state.variant().named_coasts:
            return True
        return state.variant().has_fleet_access(order.location)


class BuildLocationIsUnoccupiedCheck(Check):
    """No standing unit may already be at the build location's parent
    province."""

    MESSAGE = "Build location is already occupied."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, BuildOrder)
        parent = state.variant().parent_of(order.location)
        return not state.province(parent).is_occupied()


# Adjustment-phase disband checks (DATC 6.J.3–6.J.11). Civil disorder is
# resolved by a separate reducer, not by static checks here.


class AdjustmentDisbandUnitExistsCheck(Check):
    """A standing unit of the ordering nation must exist at the order's
    location for an Adjustment-phase Disband to be legal."""

    MESSAGE = "No unit of this nation exists at the source location."

    @classmethod
    def check(cls, state: "StateView", order: Order) -> bool:
        assert isinstance(order, AdjustmentDisbandOrder)
        unit = state.units().standing_by_loc().get(order.location)
        return unit is not None and unit.nation == order.nation


# === Order classes ===


@dataclass(frozen=True)
class HoldOrder(Order):
    """A non-dislodged unit's instruction to stay put during the Movement
    phase. Hold has no legality requirements — staying in place is
    always legal — so LEGALITY_CHECKS is empty."""

    nation: str
    source: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = ()

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class MoveOrder(Order):
    """A standing unit's instruction to relocate to an adjacent province
    during the Movement phase (DATC 6.A). Convoyed moves are out of scope
    for the prototype — only directly-adjacent targets are reachable.
    Head-to-head pairs are detected during strength resolution and
    contested via attack vs. defense strength rather than as two
    independent attacks."""

    nation: str
    source: str
    target: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        MoveTargetIsNotSourceCheck,
        MoveTargetIsReachableCheck,
    )

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class SupportHoldOrder(Order):
    """A standing unit's instruction to lend defensive strength to another
    unit holding at `supported_source` (DATC 6.A.13, 6.D.7). Whether the
    support is *matched* (the supported unit is actually holding, not
    moving) and whether it is *cut* (a foreign attack on the supporter)
    are computed during MatchSupports / ResolveStrengthsAndCuts."""

    nation: str
    source: str
    supported_source: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        SupportHoldNotSelfSupportCheck,
        SupportHoldHasSupportedUnitCheck,
        SupportHoldSupporterCanReachCheck,
    )

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class SupportMoveOrder(Order):
    """A standing unit's instruction to lend attack strength to another
    unit moving from `supported_source` to `target` (DATC 6.A.13, 6.D.5,
    6.D.6, 6.D.7). Matched/cut status is resolved as for SupportHold;
    additionally, an attack from the support's own target province does
    not cut the support (DATC 6.D.4)."""

    nation: str
    source: str
    supported_source: str
    target: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        SupportMoveNotIntoSelfCheck,
        SupportMoveHasSupportedUnitCheck,
        SupportMoveSupporterCanReachCheck,
        SupportMoveSupportedCanReachCheck,
    )

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class ConvoyOrder(Order):
    """A fleet's instruction to convoy an army from one coastal province
    to another during the Movement phase (DATC 6.F, 6.G). The convoyed
    army submits its own MoveOrder; this order describes one fleet's
    participation in carrying that army.

    The presence of one or more matched, non-disrupted ConvoyOrders is
    what makes a non-adjacent army Move legal. A ConvoyOrder is
    *matched* (analogous to a matched Support) when there is a
    corresponding MoveOrder for an Army at `army_source` moving to
    `army_target`. Matching is computed by MatchConvoysReducer (added
    in C2), not by a static check.

    A ConvoyOrder may only be issued by a Fleet in a sea province. The
    fleet's survival through the Movement phase governs whether the
    convoy is *disrupted*; disruption is resolved by the Decision graph
    (in C3), not statically.

    C1 establishes only the parsed form and the static legality
    requirements. Convoy paths and integration into Move resolution
    arrive in C2 and C3."""

    nation: str
    source: str
    army_source: str
    army_target: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        ConvoyerIsFleetCheck,
        ConvoyerIsInSeaCheck,
        ConvoyArmyExistsCheck,
        ConvoyArmyIsArmyCheck,
        ConvoyEndpointsAreCoastalCheck,
        ConvoyEndpointsDifferCheck,
        ConvoyFleetReachesEndpointsCheck,
    )

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class RetreatOrder(Order):
    """A dislodged unit's instruction to relocate to an adjacent
    unoccupied non-contested province (DATC 6.H.1–6.H.6). Bounce
    resolution between competing retreats is handled separately by
    the `resolve_retreat_bounces` reducer, not by a static check."""

    nation: str
    source: str
    target: str
    unit_type: str
    dislodged_from: Optional[str]

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        RetreatTargetIsReachableCheck,
        RetreatTargetIsUnoccupiedCheck,
        RetreatNotToAttackerOriginCheck,
        RetreatTargetIsNotContestedCheck,
    )

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class DisbandOrder(Order):
    """A dislodged unit's instruction to disband instead of retreating.
    Always legal. The Adjustment-phase form of disband is out of scope
    for the prototype."""

    nation: str
    source: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = ()

    def source_province(self) -> str:
        return self.source


@dataclass(frozen=True)
class BuildOrder(Order):
    """An Adjustment-phase instruction to add a new unit at one of the
    nation's vacant home supply centers (or any owned supply center if
    the variant allows non-home builds). Per-nation count enforcement
    (excess builds beyond the allowed total) is handled by the
    `enforce_build_limits` reducer, not by a static check."""

    nation: str
    location: str
    unit_type: Optional[str]

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        BuildUnitTypeIsValidCheck,
        BuildLocationIsSupplyCenterCheck,
        BuildLocationIsOwnedCheck,
        BuildLocationIsHomeCenterCheck,
        BuildArmyNotAtNamedCoastCheck,
        BuildFleetCoastIsSpecifiedCheck,
        BuildFleetLocationIsCoastalCheck,
        BuildLocationIsUnoccupiedCheck,
    )

    def source_province(self) -> str:
        return self.location


@dataclass(frozen=True)
class AdjustmentDisbandOrder(Order):
    """An Adjustment-phase instruction to remove an existing standing unit
    of the ordering nation. Distinct from the Retreat-phase DisbandOrder:
    Adjustment disbands carry an explicit unit reference (nation +
    location + unit_type captured at parse time) and have their own
    legality checks. Per-nation count enforcement (excess disbands beyond
    the required total) is handled by the `enforce_disband_limits`
    reducer, not by a static check."""

    nation: str
    location: str
    unit_type: str

    LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]] = (
        AdjustmentDisbandUnitExistsCheck,
    )

    def source_province(self) -> str:
        return self.location


# === State ===


@dataclass(frozen=True)
class OrderResolution:
    """Per-order resolution record. Indexed parallel to parsed_orders.

    Lifecycle: every field starts at its default (None); fields are
    populated by the resolution reducers (ApplyLegalityChecks,
    MatchSupports, ResolveStrengthsAndCuts, ResolveRetreatBounces,
    EnforceBuildLimits, EnforceDisbandLimits, FinalizeStatuses). After
    FinalizeStatuses, `status` is guaranteed non-None and one of
    Status.{OK,ILLEGAL,BOUNCE,CUT}."""

    status: Optional[str] = None
    """Per-order resolution status. None means undecided; final values
    are Status.OK / ILLEGAL / BOUNCE / CUT. Populated incrementally by
    legality checks, retreat bounces, build/disband limits, the strength
    resolver, and FinalizeStatuses."""

    failure_reason: Optional[str] = None
    """Per-order failure message. Populated alongside ILLEGAL / BOUNCE
    statuses; None for OK orders."""

    support_matched: Optional[bool] = None
    """Per-Support-order match flag. None for non-Support and for ILLEGAL
    Support orders; True/False otherwise. A Support is matched only when
    the supported unit is actually doing what the Support claims (DATC
    6.D.7, 6.D.28). Populated by MatchSupportsReducer."""

    convoy_matched: Optional[bool] = None
    """Per-ConvoyOrder match flag. None for non-Convoy and for ILLEGAL
    Convoy orders; True/False otherwise. A Convoy is matched iff there
    is a non-ILLEGAL MoveOrder from `army_source` to `army_target` whose
    target province matches the convoy's named endpoint (parent-province
    match accepted, since convoy endpoints are parents and move targets
    may carry named-coast information that resolves to the same parent).
    Populated by MatchConvoysReducer."""

    via_convoy: bool = False
    """Per-MoveOrder flag indicating the move resolves via convoy rather
    than direct adjacency. Populated by MarkConvoyedMovesReachableReducer
    when it un-marks an ILLEGAL-reachability Move because a static convoy
    path exists. Read by the strength solver to determine which Moves
    need convoy-path-intact checks and by head-to-head detection to
    exclude convoyed moves (DATC 6.G). Defaults to False; only True for
    Moves that resolved their reachability via convoy."""

    convoy_path_intact: Optional[bool] = None
    """Per-convoyed-MoveOrder flag indicating whether at least one path
    of matched, non-dislodged ConvoyOrders connects the move's source
    and target after resolution. None for non-convoyed Moves; True/False
    for convoyed Moves once the solver terminates. Populated by the
    strength solver (resolution.py)."""

    support_cut: Optional[str] = None
    """Per-Support-order cut status. None for non-Support orders;
    Status.OK (uncut) or Status.CUT otherwise. Populated by
    ResolveStrengthsAndCutsReducer; later mirrored onto status by
    FinalizeStatusesReducer for the external Resolution record."""

    attack_strength: Optional[int] = None
    """Per-MoveOrder attack strength: 1 + matched/uncut/non-defender-
    nation SupportMoves attached to this Move. None for non-Move and for
    ILLEGAL Move orders. Populated by ResolveStrengthsAndCutsReducer."""

    defense_strength: Optional[int] = None
    """Per-MoveOrder defense strength used when the move is the defender
    in a head-to-head: 1 + matched/uncut SupportMoves (no defender-nation
    drop). None for Move orders that aren't head-to-head defenders.
    Populated by ResolveStrengthsAndCutsReducer."""

    prevent_strength: Optional[int] = None
    """Per-MoveOrder prevent strength: 0 when losing a head-to-head, else
    1 + matched/uncut SupportMoves. Used to determine whether competing
    attacks into the same province stand each other off. None for non-Move
    or ILLEGAL Move orders. Populated by ResolveStrengthsAndCutsReducer."""

    hold_strength: Optional[int] = None
    """Per-order hold strength at the order's source province: 0 if the
    unit's own Move resolved OK (vacating), else 1 + matched/uncut
    SupportHolds. None for non-Movement orders. Populated by
    ResolveStrengthsAndCutsReducer."""


@dataclass(frozen=True)
class AdjudicationState:
    """The complete working state for one phase resolution.

    The state is unified across phases — phase-specific fields (parsed
    builds, retreats, contested provinces) all live on the same class.
    Fields unused by a given phase remain at their empty defaults. This
    keeps the type uniform; per-phase state classes can be introduced
    later if the unified form becomes unwieldy.

    Each field is one of three lifecycle categories:
      - input  : set at construction from the external State; never modified
      - parsed : populated by a parse_* reducer; consumed by later reducers
      - output : populated by a resolution / outcome reducer; consumed when
                 the engine builds the external return State(s)
    """

    # --- inputs (set at construction; populated by Engine._to_adjudication_state) ---

    variant: Variant
    """The variant definition — adjacency graph, supply centers, modifiers."""

    phase: Phase
    """The phase being resolved. Selects which PhaseResolver runs."""

    units: Tuple[Unit, ...]
    """All units on the board, both standing and dislodged."""

    supply_centers: Tuple[SupplyCenter, ...]
    """Current supply-center ownership."""

    raw_orders: Tuple[RawOrder, ...]
    """Wire-format orders submitted by players, untyped and unvalidated."""

    contested_provinces: Tuple[str, ...]
    """Parent provinces that stood off during the preceding Movement phase.
    Empty outside the Retreat phase."""

    # --- parsed forms (populated by parse_movement_orders / parse_retreat_orders /
    # parse_adjustment_orders) ---

    parsed_orders: Tuple[Order, ...] = ()
    """Typed Order instances in submission order, plus any default orders
    inferred for unaccompanied dislodged units (Retreat -> Disband) or
    unordered standing units (Movement -> Hold)."""

    # --- resolution outputs (populated in order by apply_legality_checks,
    # resolve_retreat_bounces, enforce_build_limits, enforce_disband_limits,
    # apply_civil_disorder, finalize_statuses) ---

    resolutions: Tuple[OrderResolution, ...] = ()
    """Per-order resolution record, indexed parallel to parsed_orders.
    Populated incrementally by the resolution reducers. After
    FinalizeStatuses, every entry's `status` is one of
    Status.{OK,ILLEGAL,BOUNCE,CUT}."""

    civil_disorder_disbands: Tuple[str, ...] = ()
    """Locations of units selected for civil-disorder disband in the
    Adjustment phase. Populated by ApplyCivilDisorderReducer; consumed by
    ApplyAdjustmentOutcomesReducer to remove these units from the next
    state. Empty outside Adjustment."""

    auto_rebuild_units: Tuple[Unit, ...] = ()
    """Units to be auto-built for non-playable nations with rebuilds=True.
    Populated by ApplyNonPlayableRebuildsReducer; consumed by
    ApplyAdjustmentOutcomesReducer to add these units to next_units.
    Empty outside Adjustment."""

    # --- outcome (populated by apply_*_outcomes; consumed by Engine return) ---

    next_units: Tuple[Unit, ...] = ()
    """The units list as it should appear after this phase resolves —
    movements applied, disbanded units removed, builds added, dislodged
    flags cleared as appropriate."""

    next_contested_provinces: Tuple[str, ...] = ()
    """Parent provinces where two or more legal Moves bounced this phase.
    Populated by ApplyMovementOutcomes; empty outside Movement. Carried
    forward by the Engine into the next phase's State.contested_provinces."""

    next_supply_centers: Tuple[SupplyCenter, ...] = ()
    """Supply-center ownership as it should appear after this phase
    resolves. Populated by UpdateSupplyCenterOwnership (Retreat phase
    only): recomputed from post-retreat unit positions when the next
    phase is Adjustment, copied through unchanged otherwise. Empty
    until that reducer runs; consumed by the Engine when building the
    next phase's State."""


# === Views ===


class ProvinceView:
    """Read-only wrapper over (AdjudicationState, parent province id) for
    questions about one specific parent province."""

    def __init__(self, state: AdjudicationState, parent: str):
        self._state = state
        self._parent = parent

    def is_occupied(self) -> bool:
        for unit in self._state.units:
            if unit.dislodged:
                continue
            if self._state.variant.parent_of(unit.location) == self._parent:
                return True
        return False

    def is_sea(self) -> bool:
        """True iff this province is a sea province. Named coasts and
        inland provinces are not sea provinces; coastal land provinces
        are not sea provinces. A fleet can occupy a sea province
        directly."""
        province = self._state.variant.provinces.get(self._parent)
        return province is not None and province.type == ProvinceType.SEA

    def is_coastal(self) -> bool:
        """True iff this province is a coastal land province — a land
        province with at least one fleet-passable adjacency. Sea
        provinces are not coastal; inland land provinces are not
        coastal. Convoy endpoints (army_source / army_target on a
        ConvoyOrder) must be coastal."""
        province = self._state.variant.provinces.get(self._parent)
        if province is None or province.type == ProvinceType.SEA:
            return False
        return self._state.variant.has_fleet_access(self._parent)


class NationView:
    """Read-only wrapper over (AdjudicationState, nation id) for
    questions about one specific nation."""

    def __init__(self, state: AdjudicationState, nation: str):
        self._state = state
        self._nation = nation

    def owned_supply_centers(self) -> frozenset:
        return frozenset(
            sc.province
            for sc in self._state.supply_centers
            if sc.nation == self._nation
        )

    def home_supply_centers(self) -> frozenset:
        """Provinces statically assigned to this nation as home
        supply centres by the variant, regardless of current
        ownership. Matches godip's Graph().SCs(n), which is the
        source set used by SortedUnits for civil-disorder distance."""
        return frozenset(
            pid
            for pid, province in self._state.variant.provinces.items()
            if province.home_nation == self._nation
        )

    def standing_unit_count(self) -> int:
        return sum(
            1 for u in self._state.units if u.nation == self._nation and not u.dislodged
        )

    def allowed_builds(self) -> int:
        if self._is_non_playable():
            return 0
        return max(0, len(self.owned_supply_centers()) - self.standing_unit_count())

    def required_disbands(self) -> int:
        if self._is_non_playable():
            return 0
        return max(0, self.standing_unit_count() - len(self.owned_supply_centers()))

    def _is_non_playable(self) -> bool:
        for nation in self._state.variant.nations:
            if nation.id == self._nation:
                return nation.non_playable
        return False

    def civil_disorder_ranking(self) -> Tuple[Unit, ...]:
        """Units of this nation ordered for civil-disorder selection:
        furthest-from-home-SC first, fleets before armies on ties,
        location id alphabetical on further ties. Mirrors godip's
        SortedUnits (phase.go) — sort by shortestDistance to the
        nation's home supply centres (Graph().SCs(n)) descending,
        with Fleet-before-Army and province-id alphabetical tie
        breaks. Adjacency is unweighted regardless of pass type:
        godip's shortestDistance keeps the minimum of a type-filtered
        and an unfiltered path lookup, and the unfiltered (raw-graph)
        path is always at least as short."""
        units = tuple(
            u for u in self._state.units
            if u.nation == self._nation and not u.dislodged
        )
        if not self.home_supply_centers():
            return tuple(
                sorted(
                    units,
                    key=lambda u: (0 if u.type == Unit.FLEET else 1, u.location),
                )
            )
        distances = self._distance_from_home()
        variant = self._state.variant
        def unit_distance(unit: Unit) -> int:
            if unit.location in distances:
                return distances[unit.location]
            return distances.get(variant.parent_of(unit.location), 0)
        return tuple(
            sorted(
                units,
                key=lambda u: (
                    -unit_distance(u),
                    0 if u.type == Unit.FLEET else 1,
                    u.location,
                ),
            )
        )

    def _bfs_source_nodes(self) -> set:
        """Build the BFS source set for civil-disorder distance
        computation: every home supply center of this nation, plus
        every named coast belonging to one of those provinces. Named
        coasts are included because a fleet can occupy a coast and
        we want its distance measured from that coast, not from the
        parent."""
        variant = self._state.variant
        home = self.home_supply_centers()
        sources: set = set(home)
        for province_id in home:
            for coast in variant.coasts_of(province_id):
                sources.add(coast)
        return sources

    def _distance_from_home(self) -> Dict[str, int]:
        """Unweighted BFS distance from each reachable node to the
        nearest home supply center of this nation (or named coast
        thereof). Pass type is ignored — distances are over the raw
        adjacency graph, matching the effective behaviour of godip's
        shortestDistance (whose unfiltered path is always at least
        as short as the type-filtered one). Returns a map from node
        id to distance; unreachable nodes are absent."""
        variant = self._state.variant
        sources = self._bfs_source_nodes()
        if not sources:
            return {}
        distances: Dict[str, int] = {node: 0 for node in sources}
        frontier: set = set(sources)
        depth = 0
        while frontier:
            depth += 1
            next_frontier: set = set()
            for node in frontier:
                for adjacency in variant.adjacencies_of(node):
                    neighbour = adjacency.to
                    if neighbour in distances:
                        continue
                    distances[neighbour] = depth
                    next_frontier.add(neighbour)
            frontier = next_frontier
        return distances


class UnitsView:
    """Read-only wrapper over AdjudicationState providing queries grouped
    over the units list as a whole."""

    def __init__(self, state: AdjudicationState):
        self._state = state

    def all(self) -> Tuple[Unit, ...]:
        return self._state.units

    def standing_by_loc(self) -> Dict[str, Unit]:
        return {u.location: u for u in self._state.units if not u.dislodged}

    def at_parent(self, location: str) -> Optional[Unit]:
        """Look up a standing unit by parent province. Accepts either a
        bare parent province id or a named coast; in both cases a match
        is by parent. Returns the unit or None."""
        parent = self._state.variant.parent_of(location)
        for u in self._state.units:
            if u.dislodged:
                continue
            if self._state.variant.parent_of(u.location) == parent:
                return u
        return None

    def dislodged_by_loc(self) -> Dict[str, Unit]:
        return {u.location: u for u in self._state.units if u.dislodged}

    def dislodged_for_source(self, source: str) -> Optional[Unit]:
        dislodged = self.dislodged_by_loc()
        if source in dislodged:
            return dislodged[source]
        parent = self._state.variant.parent_of(source)
        for loc, unit in dislodged.items():
            if self._state.variant.parent_of(loc) == parent:
                return unit
        return None


class OrdersView:
    """Read-only wrapper over AdjudicationState providing queries grouped
    over parsed_orders."""

    def __init__(self, state: AdjudicationState):
        self._state = state

    def by_source(self) -> Dict[str, Tuple[int, Order]]:
        by_source: Dict[str, Tuple[int, Order]] = {}
        for i, order in enumerate(self._state.parsed_orders):
            if isinstance(order, (HoldOrder, MoveOrder, RetreatOrder, DisbandOrder)):
                by_source[order.source] = (i, order)
        return by_source

    def retreats_by_target_parent(self) -> Dict[str, List[int]]:
        grouped: Dict[str, List[int]] = {}
        for i, order in enumerate(self._state.parsed_orders):
            if not isinstance(order, RetreatOrder):
                continue
            if self._state.resolutions[i].status is not None:
                continue
            parent = self._state.variant.parent_of(order.target)
            grouped.setdefault(parent, []).append(i)
        return grouped

    def moves_by_target_parent(self) -> Dict[str, List[int]]:
        grouped: Dict[str, List[int]] = {}
        for i, order in enumerate(self._state.parsed_orders):
            if not isinstance(order, MoveOrder):
                continue
            if self._state.resolutions[i].status is not None:
                continue
            parent = self._state.variant.parent_of(order.target)
            grouped.setdefault(parent, []).append(i)
        return grouped


class StateView:
    """Read-only wrapper over AdjudicationState. The top-level entry
    point: every reducer and every check receives a StateView and reads
    derived data through its methods. Sub-Views are constructed on
    demand via province(), nation(), units(), and orders(). The only
    way reducers update state is through replace(), which returns a new
    StateView wrapping a freshly-constructed AdjudicationState."""

    def __init__(self, state: AdjudicationState):
        self._state = state

    def variant(self) -> Variant:
        return self._state.variant

    def phase(self) -> Phase:
        return self._state.phase

    def raw_orders(self) -> Tuple[RawOrder, ...]:
        return self._state.raw_orders

    def supply_centers(self) -> Tuple[SupplyCenter, ...]:
        return self._state.supply_centers

    def contested_provinces(self) -> frozenset:
        return frozenset(self._state.contested_provinces)

    def next_contested_provinces(self) -> Tuple[str, ...]:
        return self._state.next_contested_provinces

    def next_units(self) -> Tuple[Unit, ...]:
        return self._state.next_units

    def next_supply_centers(self) -> Tuple[SupplyCenter, ...]:
        return self._state.next_supply_centers

    def civil_disorder_disbands(self) -> Tuple[str, ...]:
        return self._state.civil_disorder_disbands

    def auto_rebuild_units(self) -> Tuple[Unit, ...]:
        return self._state.auto_rebuild_units

    def parsed_orders(self) -> Tuple[Order, ...]:
        return self._state.parsed_orders

    def resolutions(self) -> Tuple[OrderResolution, ...]:
        return self._state.resolutions

    def province(self, parent: str) -> ProvinceView:
        return ProvinceView(self._state, parent)

    def nation(self, nation: str) -> NationView:
        return NationView(self._state, nation)

    def units(self) -> UnitsView:
        return UnitsView(self._state)

    def orders(self) -> OrdersView:
        return OrdersView(self._state)

    def next_phase(self) -> Optional[Phase]:
        phase = self._state.phase
        fallback: Optional[PhaseTransition] = None
        for transition in self._state.variant.phase_progression.transitions:
            if (
                transition.from_season != phase.season
                or transition.from_type != phase.type
            ):
                continue
            if transition.year_mod is not None:
                if phase.year % transition.year_mod == transition.year_mod_value:
                    return Phase(
                        season=transition.to_season,
                        year=phase.year + transition.year_delta,
                        type=transition.to_type,
                    )
            elif fallback is None:
                fallback = transition
        if fallback is not None:
            return Phase(
                season=fallback.to_season,
                year=phase.year + fallback.year_delta,
                type=fallback.to_type,
            )
        return None

    def replace(self, **kwargs) -> "StateView":
        return StateView(replace(self._state, **kwargs))

    @property
    def raw(self) -> AdjudicationState:
        return self._state
