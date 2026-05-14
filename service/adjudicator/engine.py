from __future__ import annotations

import abc
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Tuple, Type

from .domain import (
    OrderOption,
    Outcome,
    Phase,
    ProvinceType,
    Resolution,
    State,
    Unit,
    Variant,
)

# === Constants ===


class OrderType:
    HOLD = "Hold"
    MOVE = "Move"
    SUPPORT = "Support"
    CONVOY = "Convoy"
    BUILD = "Build"
    DISBAND = "Disband"
    RETREAT = "Retreat"


class ResolutionType:
    OK = "OK"
    BOUNCE = "BOUNCE"
    ILLEGAL = "ILLEGAL"
    CUT = "CUT"


# Sentinel returned by Decision._decide to signal "dependencies not yet ready".
_UNDECIDED: Any = object()


# === Engine ===


class Engine:
    """
    Public API for the adjudication engine.
    """

    def __init__(self, variant: Variant):
        self.variant = variant
        self.options_builder = OptionsBuilder(variant)

    def adjudicate(self, state: State) -> List[State]:
        """
        Resolve the orders for a phase and advance to the next phase
        requiring player input.

        Returns a list of GameStates: the input state with `resolutions`
        populated, zero or more skipped intermediate phases (Retreat with
        no dislodgements, Adjustment with balanced SC / unit counts), and
        the next phase requiring input with `resolutions=None`. If an
        Adjustment phase resolution triggers a solo victory, the
        triggering GameState carries `outcome` and no further GameStates
        are generated.
        """
        results: List[State] = []
        current = state
        is_skip = False
        while True:
            produced = PhaseResolver.for_state(current, self.variant).resolve()
            resolved = produced[0]
            if is_skip:
                resolved.skipped = True
                resolved.resolutions = []
            results.append(resolved)
            if resolved.phase.type == Phase.ADJUSTMENT:
                outcome = self._solo_outcome(resolved)
                if outcome is not None:
                    resolved.outcome = outcome
                    return results
            if len(produced) < 2:
                return results
            next_state = produced[1]
            if not self._is_skippable(next_state):
                results.append(next_state)
                return results
            current = next_state
            is_skip = True

    def _is_skippable(self, state: State) -> bool:
        if state.phase.type == Phase.RETREAT:
            return not any(unit.dislodged for unit in state.units)
        if state.phase.type == Phase.ADJUSTMENT:
            return self._adjustment_is_balanced(state)
        return False

    def _adjustment_is_balanced(self, state: State) -> bool:
        owned: Dict[str, int] = {}
        for sc in state.supply_centers:
            owned[sc.nation] = owned.get(sc.nation, 0) + 1
        units: Dict[str, int] = {}
        for unit in state.units:
            if unit.dislodged:
                continue
            units[unit.nation] = units.get(unit.nation, 0) + 1
        for nation in set(owned) | set(units):
            if owned.get(nation, 0) != units.get(nation, 0):
                return False
        return True

    def _solo_outcome(self, state: State) -> Optional[Outcome]:
        threshold = self.variant.solo_victory_supply_centers
        owned: Dict[str, int] = {}
        for sc in state.supply_centers:
            owned[sc.nation] = owned.get(sc.nation, 0) + 1
        winners = tuple(
            nation for nation, _ in sorted(owned.items(), key=lambda kv: (-kv[1], kv[0]))
            if owned[nation] >= threshold
        )
        if not winners:
            return None
        return Outcome(winners=winners, reason="solo", year=state.phase.year)

    def get_options(self, state: State) -> List[OrderOption]:
        """
        Enumerate every legal order any unit can issue this phase.

        The flat list is the union of options across all non-dislodged
        units; each option self-describes (source / order type / target /
        aux / unit type / named coast).
        """
        return self.options_builder.build(state)


# === Legality checks ===


class LegalityCheck(abc.ABC):
    """
    A single named legality rule. Subclasses define one yes/no condition
    and the user-facing message to show when it fails. Orders compose a
    list of LegalityChecks via `LEGALITY_CHECKS`; the first failing check's
    message becomes the order's `failure_reason`.
    """

    MESSAGE: ClassVar[str] = ""

    @abc.abstractmethod
    def passes(
        self,
        order: "Order",
        variant: Variant,
        units_by_loc: Dict[str, Unit],
        orders_by_loc: Dict[str, "Order"],
    ) -> bool:
        """Whether the order satisfies this check."""
        ...


class MoveTargetIsNotSource(LegalityCheck):
    MESSAGE = "A unit can't move to its own location."

    def passes(self, order: "MoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return order.target != order.unit.location


class MoveTargetIsReachable(LegalityCheck):
    MESSAGE = "The unit can't reach the target province."

    def passes(self, order: "MoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        if variant.can_move(order.unit.location, order.target, order.unit.type):
            return True
        if order.unit.type == Unit.ARMY and order.requires_convoy:
            # A non-adjacent move is illegal only when no fleet could ever
            # have convoyed it. If fleets are positioned to convoy but were
            # ordered otherwise, the move is a failed convoy, not an illegal
            # order — the army still tried to move (DATC 6.D.8 vs 6.D.32).
            finder = ConvoyPathFinder(variant, orders_by_loc)
            return finder.could_be_convoyed(
                order.unit.location, order.target, units_by_loc
            )
        return False


class SupportHoldNotSelfSupport(LegalityCheck):
    MESSAGE = "A unit can't support itself."

    def passes(self, order: "SupportHoldOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.parent_of(order.supported_source) != variant.parent_of(order.unit.location)


class SupportHoldHasSupportedUnit(LegalityCheck):
    MESSAGE = "There's no unit at the supported province."

    def passes(self, order: "SupportHoldOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return _unit_at(variant, units_by_loc, order.supported_source) is not None


class SupportHoldSupporterCanReach(LegalityCheck):
    MESSAGE = "The supporting unit can't reach the supported province."

    def passes(self, order: "SupportHoldOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.can_support_to(
            order.unit.location, order.supported_source, order.unit.type
        )


class SupportMoveNotIntoSelf(LegalityCheck):
    MESSAGE = "A unit can't support an attack into its own province."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.parent_of(order.target) != variant.parent_of(order.unit.location)


class SupportMoveSupporterCanReach(LegalityCheck):
    MESSAGE = "The supporting unit can't reach the target."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.can_support_to(order.unit.location, order.target, order.unit.type)


class SupportMoveHasSupportedUnit(LegalityCheck):
    MESSAGE = "There's no unit at the supported source province."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return _unit_at(variant, units_by_loc, order.supported_source) is not None


class SupportMoveSupportedCanReach(LegalityCheck):
    MESSAGE = "The supported unit can't itself reach the target."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        supported = _unit_at(variant, units_by_loc, order.supported_source)
        if supported is None:
            return True
        if variant.can_move(supported.location, order.target, supported.type):
            return True
        target_parent = variant.parent_of(order.target)
        if target_parent != order.target and variant.can_move(
            supported.location, target_parent, supported.type
        ):
            return True
        for coast in variant.coasts_of(target_parent):
            if coast != order.target and variant.can_move(
                supported.location, coast, supported.type
            ):
                return True
        if supported.type == Unit.ARMY:
            finder = ConvoyPathFinder(variant, orders_by_loc)
            return finder.path_exists(supported.location, order.target)
        return False


def _unit_at(variant: Variant, units_by_loc: Dict[str, Unit], location: str) -> Optional[Unit]:
    """
    Strict unit-by-location lookup used for support / supported-unit
    legality checks. An exact match wins; otherwise, when `location` is
    a parent province, a unit at any of its named coasts also matches
    (DATC 6.B.8). A specific named coast that doesn't match exactly does
    NOT fall back to the unit's actual coast (DATC 6.B.9).
    """
    unit = units_by_loc.get(location)
    if unit is not None:
        return unit
    if location not in variant.named_coasts:
        for loc, candidate in units_by_loc.items():
            if variant.parent_of(loc) == location:
                return candidate
    return None


def _unit_for_source(variant: Variant, units_by_loc: Dict[str, Unit], source: str) -> Optional[Unit]:
    """
    Lenient unit lookup for the source of a wire-format order. An exact
    match wins; otherwise, any unit at the same parent province matches,
    even when the order specifies the wrong named coast (DATC 6.B.10).
    """
    unit = units_by_loc.get(source)
    if unit is not None:
        return unit
    parent = variant.parent_of(source)
    for loc, candidate in units_by_loc.items():
        if variant.parent_of(loc) == parent:
            return candidate
    return None


class ConvoyIssuedByFleet(LegalityCheck):
    MESSAGE = "Only fleets can convoy."

    def passes(self, order: "ConvoyOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return order.unit.type == Unit.FLEET


class ConvoyFleetIsInSeaProvince(LegalityCheck):
    MESSAGE = "A convoying fleet must be in a sea province."

    def passes(self, order: "ConvoyOrder", variant, units_by_loc, orders_by_loc) -> bool:
        province = variant.provinces.get(order.unit.location)
        if province is None:
            return False
        return province.type == ProvinceType.SEA


class ConvoyTargetsAnArmy(LegalityCheck):
    MESSAGE = "Only armies can be convoyed."

    def passes(self, order: "ConvoyOrder", variant, units_by_loc, orders_by_loc) -> bool:
        army = units_by_loc.get(order.army_source)
        return army is not None and army.type == Unit.ARMY


class ConvoyDestinationIsLand(LegalityCheck):
    MESSAGE = "A convoy target must be a non-sea province."

    def passes(self, order: "ConvoyOrder", variant, units_by_loc, orders_by_loc) -> bool:
        province = variant.provinces.get(order.target)
        if province is None:
            return False
        return province.type != ProvinceType.SEA


# === Order classes ===


class Order(abc.ABC):
    """
    A player's instruction for a unit in a single phase.

    Concrete subclasses (HoldOrder, MoveOrder, SupportOrder, …) register
    themselves against a wire-format order-type id via @Order.register.
    The `from_wire` classmethod is the only constructor used by the engine;
    direct instantiation of subclasses outside tests is rare.
    """

    # Maps the wire-format order-type id (e.g. OrderType.MOVE) to the Order subclass.
    _registry: ClassVar[Dict[str, Type["Order"]]] = {}

    # Ordered list of legality checks. First failure wins; its MESSAGE
    # becomes the order's `failure_reason`. Order subclasses override.
    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = []

    def __init__(self, unit: Optional[Unit]) -> None:
        self.unit = unit
        self.status: Optional[str] = None
        self.failure_reason: Optional[str] = None

    @classmethod
    def register(cls, order_type: str):
        """
        Decorator that registers an Order subclass under a wire-format
        order-type id (e.g. OrderType.MOVE). Applied at class definition
        time as @Order.register("Move").
        """

        def decorator(subclass):
            cls._registry[order_type] = subclass
            return subclass

        return decorator

    @classmethod
    def from_wire(
        cls,
        order_type: str,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool = False,
    ) -> Order:
        """
        Convert wire-format order data into the appropriate Order subclass
        via the registry.

        Raises ValueError if `order_type` has no registered subclass, or
        if the wire fields are incompatible with the selected order type.
        """
        subclass = cls._registry.get(order_type)
        if subclass is None:
            raise ValueError("No Order subclass registerd for this type")
        return subclass._build(unit, target, aux, unit_type, via_convoy)

    @classmethod
    @abc.abstractmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> Order:
        """
        Construct a concrete Order from wire fields. Raises ValueError
        if the fields are incompatible with this order type — e.g. a
        Move with no target, or a Support with no target or aux.
        """
        ...

    @property
    def moves_to(self) -> Optional[str]:
        """
        The province this order's unit relocates to if it succeeds, or
        None if the order doesn't move the unit. Hold, Support, and
        Convoy all return None — only MoveOrder overrides to return its
        `target`.
        """
        return None

    def validate(
        self,
        variant: Variant,
        units_by_loc: Dict[str, Unit],
        orders_by_loc: Dict[str, "Order"],
    ) -> Optional[LegalityCheck]:
        """
        Run the order's LEGALITY_CHECKS in order and return the first
        failing LegalityCheck, or None if all pass. The caller can use the
        returned LegalityCheck's MESSAGE as a user-facing failure reason.
        """
        for check_cls in self.LEGALITY_CHECKS:
            check = check_cls()
            if not check.passes(self, variant, units_by_loc, orders_by_loc):
                return check
        return None


@Order.register(OrderType.HOLD)
class HoldOrder(Order):
    """
    An order which instructs the unit to stay in its current location.
    """

    # Hold orders have no legality requirements — staying put is always allowed.
    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = []

    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "HoldOrder":
        """
        Hold orders require only a unit. The other wire fields are
        ignored; construction never fails.
        """
        return cls(unit)


@Order.register(OrderType.MOVE)
class MoveOrder(Order):
    """
    An order which instructs the unit to move to another location.
    """

    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = [
        MoveTargetIsNotSource,
        MoveTargetIsReachable,
    ]

    def __init__(self, unit: Unit, target: str, via_convoy: bool = False) -> None:
        super().__init__(unit)
        self.target = target
        self.via_convoy = via_convoy
        self.requires_convoy = False

    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "MoveOrder":
        """
        A Move order requires a target. Raises ValueError if `target`
        is None.
        """
        if target is None:
            raise ValueError("Target must be provided for a Move order")
        return cls(unit, target, via_convoy)

    @property
    def moves_to(self) -> Optional[str]:
        return self.target

    def set_convoy_info(
        self, variant: Variant, finder: "ConvoyPathFinder"
    ) -> None:
        """
        Set `requires_convoy` based on the army's intent and topology.
        Only armies are convoyed. For non-adjacent moves the army goes
        by convoy by definition. For adjacent moves the convoy is only
        used when intent is explicit — either the order is "via convoy"
        or an own-nation fleet has ordered the convoy.
        """
        if self.unit.type != Unit.ARMY:
            self.requires_convoy = False
            return
        if self.target == self.unit.location:
            self.requires_convoy = False
            return
        if not variant.is_convoyable(self.unit.location, self.target):
            self.requires_convoy = False
            return
        direct = variant.can_move(self.unit.location, self.target, Unit.ARMY)
        if not direct:
            self.requires_convoy = True
            return
        if self.via_convoy:
            self.requires_convoy = True
            return
        if finder.has_own_convoy(self.unit.location, self.target, self.unit.nation):
            self.requires_convoy = True
            return
        self.requires_convoy = False


@Order.register(OrderType.SUPPORT)
class SupportOrder(Order):
    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "SupportOrder":
        """
        A Support order requires an `aux` (the supported unit's
        province). `target` distinguishes the support type:
          - `target is None`: SupportHoldOrder — supports the unit
            holding in `aux` (DATC notation: "S X").
          - `target is not None`: SupportMoveOrder — supports the unit
            in `aux` moving to `target` (DATC notation: "S X - Y").
            If `target == aux` the move is X-X, which will fail the
            self-move legality check.
        """
        if aux is None:
            raise ValueError("Support order requires aux")
        if target is None:
            return SupportHoldOrder(unit, supported_source=aux)
        return SupportMoveOrder(unit, supported_source=aux, target=target)

    @abc.abstractmethod
    def cut_exception_location(self) -> Optional[str]:
        """
        Province an attack from which does NOT cut this support, if any.
        """
        ...


class SupportHoldOrder(SupportOrder):
    """
    An order which instructs the unit to support another unit to stay in
    the same location.
    """

    # Order matters: the "no unit at supported province" message is more
    # actionable than "can't reach", so check support existence before reach.
    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = [
        SupportHoldNotSelfSupport,
        SupportHoldHasSupportedUnit,
        SupportHoldSupporterCanReach,
    ]

    def __init__(self, unit: Unit, supported_source: str) -> None:
        super().__init__(unit)
        self.supported_source = supported_source

    def cut_exception_location(self) -> Optional[str]:
        """
        Hold supports have no cut exception — any foreign attacker cuts them.
        """
        return None


class SupportMoveOrder(SupportOrder):
    """
    An order which instructs the unit to support another unit to move to
    another location.
    """

    # Order matters: list checks so the most user-actionable failure wins.
    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = [
        SupportMoveNotIntoSelf,
        SupportMoveHasSupportedUnit,
        SupportMoveSupporterCanReach,
        SupportMoveSupportedCanReach,
    ]

    def __init__(self, unit: Unit, supported_source: str, target: str) -> None:
        super().__init__(unit)
        self.supported_source = supported_source
        self.target = target

    def cut_exception_location(self) -> Optional[str]:
        """
        Support cannot be cut from the target province.
        """
        return self.target


@Order.register(OrderType.CONVOY)
class ConvoyOrder(Order):
    """
    An order which instructs a fleet to convoy an army between two
    coastal provinces. Convoying fleets must sit in sea provinces and
    form a connected chain from the army's source to the destination.
    """

    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = [
        ConvoyIssuedByFleet,
        ConvoyFleetIsInSeaProvince,
        ConvoyTargetsAnArmy,
        ConvoyDestinationIsLand,
    ]

    def __init__(self, unit: Unit, army_source: str, target: str) -> None:
        super().__init__(unit)
        self.army_source = army_source
        self.target = target

    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "ConvoyOrder":
        if target is None or aux is None:
            raise ValueError("Convoy order requires target and aux")
        return cls(unit, army_source=aux, target=target)


# === Retreat-phase orders ===


class RetreatTargetIsReachable(LegalityCheck):
    MESSAGE = "The unit can't reach the retreat destination."

    def passes(self, order: "RetreatOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.can_move(order.unit.location, order.target, order.unit.type)


class RetreatTargetIsUnoccupied(LegalityCheck):
    MESSAGE = "There is already a unit at the retreat destination."

    def passes(self, order: "RetreatOrder", variant, units_by_loc, orders_by_loc) -> bool:
        for loc in units_by_loc:
            if variant.parent_of(loc) == variant.parent_of(order.target):
                return False
        return True


class RetreatNotToAttackerOrigin(LegalityCheck):
    MESSAGE = "A unit can't retreat to the province its attacker came from."

    def passes(self, order: "RetreatOrder", variant, units_by_loc, orders_by_loc) -> bool:
        if order.unit.dislodged_from is None:
            return True
        return variant.parent_of(order.target) != variant.parent_of(order.unit.dislodged_from)


@Order.register(OrderType.RETREAT)
class RetreatOrder(Order):
    """
    A dislodged unit's instruction to relocate to an adjacent unoccupied
    province. Retreat targets are restricted further by the per-state
    `contested_provinces` set and the unit's `dislodged_from` field; those
    restrictions are enforced by the retreat-phase resolver, not by the
    static LEGALITY_CHECKS list, because they depend on game-state context
    that isn't passed to LegalityCheck.passes.
    """

    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = [
        RetreatTargetIsReachable,
        RetreatTargetIsUnoccupied,
        RetreatNotToAttackerOrigin,
    ]

    def __init__(self, unit: Unit, target: str) -> None:
        super().__init__(unit)
        self.target = target

    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "RetreatOrder":
        if target is None:
            raise ValueError("Retreat order requires target")
        return cls(unit, target)

    @property
    def moves_to(self) -> Optional[str]:
        return self.target


@Order.register(OrderType.DISBAND)
class DisbandOrder(Order):
    """
    Disband an existing unit. Issued in two distinct contexts: by a
    dislodged unit during the Retreat phase as an alternative to
    retreating, and by a power during the Adjustment phase to reduce
    its unit count to match its supply-center count.
    """

    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = []

    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "DisbandOrder":
        return cls(unit)


# === Adjustment-phase orders ===


@Order.register(OrderType.BUILD)
class BuildOrder(Order):
    """
    Build a new unit at one of the power's vacant home supply centers
    (or any owned supply center if the variant declares
    `allow-builds-in-non-home-centers`). Legality is enforced by the
    AdjustmentPhaseResolver because some checks depend on the full
    set of submitted builds (e.g. duplicate target) and on aggregates
    that don't fit the static LegalityCheck protocol.
    """

    LEGALITY_CHECKS: ClassVar[List[Type[LegalityCheck]]] = []

    def __init__(
        self, nation: str, location: str, unit_type: Optional[str]
    ) -> None:
        super().__init__(unit=None)
        self.nation = nation
        self.location = location
        self.unit_type = unit_type

    @classmethod
    def _build(
        cls,
        unit: Unit,
        target: Optional[str],
        aux: Optional[str],
        unit_type: Optional[str],
        via_convoy: bool,
    ) -> "BuildOrder":
        # Build orders are not constructed via Order.from_wire — they're
        # parsed directly by AdjustmentPhaseResolver because they have no
        # existing unit. ValueError makes this drop quietly from Movement
        # / Retreat parsing paths.
        raise ValueError("Build orders are only valid in the Adjustment phase")


# === Convoy path finding ===


class ConvoyPathFinder:
    """
    Whether a chain of matching convoy orders connects an army's source
    province to its destination, with optional exclusion of dislodged
    convoying fleets.

    The chain traverses sea provinces holding fleets that have issued a
    non-illegal Convoy order for the given (army_source, destination)
    pair. The fleet at the start of the chain must be fleet-adjacent to
    the army's coastal province (directly or via a named coast), and
    the fleet at the end must be fleet-adjacent to the destination.
    """

    def __init__(self, variant: Variant, orders_by_loc: Dict[str, "Order"]) -> None:
        self.variant = variant
        self.orders_by_loc = orders_by_loc

    def path_exists(
        self,
        army_source: str,
        destination: str,
        excluded: Optional[set] = None,
    ) -> bool:
        candidates = self._candidates(army_source, destination)
        if excluded is not None:
            candidates = candidates - excluded
        return self._chain_through(army_source, destination, candidates)

    def could_be_convoyed(
        self, army_source: str, destination: str, units_by_loc: Dict[str, Unit]
    ) -> bool:
        """
        Whether a convoy chain is physically possible — every step is a
        sea province occupied by a fleet — regardless of convoy orders.
        Distinguishes a failed convoy (the army still tried to move, so
        it can't receive hold support; DATC 6.D.8) from an illegal order
        (no fleet could ever have convoyed it; DATC 6.D.32).
        """
        occupied_seas = {
            loc
            for loc, unit in units_by_loc.items()
            if unit.type == Unit.FLEET
            and self.variant.provinces.get(loc) is not None
            and self.variant.provinces[loc].type == ProvinceType.SEA
        }
        return self._chain_through(army_source, destination, occupied_seas)

    def _chain_through(
        self, army_source: str, destination: str, sea_provinces: set
    ) -> bool:
        if army_source == destination:
            return False
        if not sea_provinces:
            return False
        frontier = {
            sea
            for sea in sea_provinces
            if self._fleet_adjacent_to_coast(sea, army_source)
        }
        visited = set(frontier)
        while frontier:
            new_frontier = set()
            for sea in frontier:
                if self._fleet_adjacent_to_coast(sea, destination):
                    return True
                for adjacency in self.variant.adjacencies_of(sea):
                    if not adjacency.allows(Unit.FLEET):
                        continue
                    neighbour = adjacency.to
                    if neighbour in sea_provinces and neighbour not in visited:
                        new_frontier.add(neighbour)
            visited.update(new_frontier)
            frontier = new_frontier
        return False

    def _candidates(self, army_source: str, destination: str) -> set:
        return {
            order.unit.location
            for order in self.orders_by_loc.values()
            if isinstance(order, ConvoyOrder)
            and order.status != ResolutionType.ILLEGAL
            and order.army_source == army_source
            and order.target == destination
        }

    def has_own_convoy(
        self, army_source: str, destination: str, nation: str
    ) -> bool:
        """
        Whether any non-illegal convoy order for this army move was
        issued by `nation`. Used to determine convoy intent for adjacent
        moves (DATC 6.G.1, 6.G.2, 6.G.5).
        """
        return any(
            isinstance(order, ConvoyOrder)
            and order.status != ResolutionType.ILLEGAL
            and order.army_source == army_source
            and order.target == destination
            and order.unit.nation == nation
            for order in self.orders_by_loc.values()
        )

    def is_on_minimal_chain(
        self, fleet_loc: str, army_source: str, destination: str
    ) -> bool:
        """
        Whether `fleet_loc` is a valid convoy for this army move.

        A convoy fleet is invalid if either:
          - Topologically impossible: there's no path through it in the
            variant's sea-province graph (DATC 6.G.7).
          - Redundant within current orders: it's on a current convoy
            chain but not on any minimum-length one (DATC 6.G.19, 6.F.12).

        A fleet that is topologically reachable but isn't part of any
        current chain is still legal (DATC 6.G.6) — the player issued a
        convoy order that just doesn't help this turn.
        """
        province = self.variant.provinces.get(fleet_loc)
        if province is None or province.type != ProvinceType.SEA:
            return False
        if not self._sea_reaches_coast(fleet_loc, army_source):
            return False
        if not self._sea_reaches_coast(fleet_loc, destination):
            return False
        return not self._is_redundant_within_orders(
            fleet_loc, army_source, destination
        )

    def _is_redundant_within_orders(
        self, fleet_loc: str, army_source: str, destination: str
    ) -> bool:
        """
        A fleet is redundant iff it sits on a longer-than-minimal chain
        among the currently-ordered convoys. A fleet that isn't on any
        current chain (only useful "in theory") is not redundant —
        DATC 6.G.6 treats such an order as still expressing intent.
        """
        candidates = self._candidates(army_source, destination)
        if fleet_loc not in candidates:
            return False
        min_len_all = self._min_chain_length(army_source, destination, candidates)
        if min_len_all is None:
            return False
        d_from = self._min_distance_from_coast(army_source, fleet_loc, candidates)
        d_to = self._min_distance_to_coast(fleet_loc, destination, candidates)
        if d_from is None or d_to is None:
            return False
        return d_from + d_to - 1 > min_len_all

    def _sea_reaches_coast(self, start_sea: str, coast_id: str) -> bool:
        """
        Whether a fleet at `start_sea` can reach `coast_id` via a chain
        of sea-only provinces in the variant graph (regardless of
        current orders).
        """
        if self._fleet_adjacent_to_coast(start_sea, coast_id):
            return True
        visited = {start_sea}
        frontier = {start_sea}
        while frontier:
            new_frontier: set = set()
            for sea in frontier:
                for adjacency in self.variant.adjacencies_of(sea):
                    if not adjacency.allows(Unit.FLEET):
                        continue
                    neighbour = adjacency.to
                    if neighbour in visited:
                        continue
                    neighbour_prov = self.variant.provinces.get(neighbour)
                    if neighbour_prov is None:
                        continue
                    if neighbour_prov.type != ProvinceType.SEA:
                        continue
                    if self._fleet_adjacent_to_coast(neighbour, coast_id):
                        return True
                    visited.add(neighbour)
                    new_frontier.add(neighbour)
            frontier = new_frontier
        return False

    def _min_chain_length(
        self, army_source: str, destination: str, candidates: set
    ) -> Optional[int]:
        """Number of fleets on the shortest chain from army_source to destination."""
        frontier = {
            sea for sea in candidates if self._fleet_adjacent_to_coast(sea, army_source)
        }
        if not frontier:
            return None
        visited = set(frontier)
        depth = 1
        while frontier:
            next_frontier: set = set()
            for sea in frontier:
                if self._fleet_adjacent_to_coast(sea, destination):
                    return depth
                for adjacency in self.variant.adjacencies_of(sea):
                    if not adjacency.allows(Unit.FLEET):
                        continue
                    if adjacency.to in candidates and adjacency.to not in visited:
                        next_frontier.add(adjacency.to)
            visited.update(next_frontier)
            frontier = next_frontier
            depth += 1
        return None

    def _min_distance_from_coast(
        self, coast_id: str, sea_target: str, candidates: set
    ) -> Optional[int]:
        """Shortest number of fleets to reach `sea_target` from `coast_id`."""
        if sea_target not in candidates:
            return None
        if self._fleet_adjacent_to_coast(sea_target, coast_id):
            return 1
        frontier = {
            sea for sea in candidates if self._fleet_adjacent_to_coast(sea, coast_id)
        }
        if not frontier:
            return None
        visited = set(frontier)
        depth = 1
        while frontier:
            if sea_target in frontier:
                return depth
            next_frontier: set = set()
            for sea in frontier:
                for adjacency in self.variant.adjacencies_of(sea):
                    if not adjacency.allows(Unit.FLEET):
                        continue
                    if adjacency.to in candidates and adjacency.to not in visited:
                        next_frontier.add(adjacency.to)
            visited.update(next_frontier)
            frontier = next_frontier
            depth += 1
        return None

    def _min_distance_to_coast(
        self, sea_source: str, coast_id: str, candidates: set
    ) -> Optional[int]:
        """Shortest number of fleets to reach `coast_id` from `sea_source`."""
        if sea_source not in candidates:
            return None
        if self._fleet_adjacent_to_coast(sea_source, coast_id):
            return 1
        frontier = {sea_source}
        visited = {sea_source}
        depth = 1
        while frontier:
            next_frontier: set = set()
            for sea in frontier:
                for adjacency in self.variant.adjacencies_of(sea):
                    if not adjacency.allows(Unit.FLEET):
                        continue
                    if adjacency.to in candidates and adjacency.to not in visited:
                        next_frontier.add(adjacency.to)
            for sea in next_frontier:
                if self._fleet_adjacent_to_coast(sea, coast_id):
                    return depth + 1
            visited.update(next_frontier)
            frontier = next_frontier
            depth += 1
        return None

    def _fleet_adjacent_to_coast(self, sea_id: str, coastal_id: str) -> bool:
        for adjacency in self.variant.adjacencies_of(sea_id):
            if not adjacency.allows(Unit.FLEET):
                continue
            if adjacency.to == coastal_id:
                return True
            named = self.variant.named_coasts.get(adjacency.to)
            if named is not None and named.parent_province == coastal_id:
                return True
        return False


# === Decision base ===


class Decision(abc.ABC):
    """
    A single value the adjudicator computes during phase resolution —
    one specific question, with one specific answer that's set exactly
    once.

    Diplomacy's resolution rules are deeply interdependent. Whether a
    support is cut depends on which attackers succeed. Whether an
    attack succeeds depends on the strength of its supporting units.
    Whether those supports apply depends on whether *they* are cut.
    A simple top-down algorithm can't compute these because the
    dependency graph contains cycles. The Decision model handles this
    by representing each question as its own object: a Decision is a
    node in a dependency graph whose value is set when (and only when)
    its dependencies are known.

    Example: `SupportCutDecision(support)` answers exactly one
    question — "is this support cut?". Its value is either
    `ResolutionType.OK` or `ResolutionType.CUT`. To compute it, the Decision
    looks at the attackers into the support's province and consults
    *their* `MoveResolutionDecision`s, which may in turn depend on
    this support. The cycle gets broken by iteration: each pass,
    whichever Decisions can resolve themselves do so; the rest wait.

    Each Decision is uniquely identified by its inputs (an Order, a
    province, a (move, target) pair, etc.). The `DecisionContext`
    holds them in typed dicts (`support_cut`, `attack_strength`, …)
    so other Decisions look them up by key.

    Resolution proceeds as a fixed-point loop. Each pass, every
    Decision that can compute its value does so via `_decide()`;
    those whose dependencies aren't ready return `_UNDECIDED` and
    wait for the next pass. When a full pass produces no new
    resolutions, the loop halts and `_default()` fills in any
    Decisions that never resolved.

    Subclasses implement two methods:
      - `_decide()` — return the value if dependencies are ready,
        otherwise `_UNDECIDED`.
      - `_default()` — return a fallback value, called once after
        the fixed-point loop stalls.

    What a Decision is **not**:
      - Not an Order. Orders are players' instructions to units;
        Decisions are the algorithm's conclusions about what those
        orders accomplish.
      - Not a state mutation. Decisions only compute values. The
        next State is rebuilt at the end (in `_finalize_statuses`
        and `_build_next_states`) by reading from resolved Decisions.
      - Not the wire-format `Resolution`. That record is derived from
        Decisions at finalisation; it carries extra information
        (status, failure_reason) that lives on the Order, not the
        Decision.
      - Not stateful across calls. Each `Adjudication` instance
        constructs its own set of Decisions; they live for exactly
        one phase resolution and are discarded afterwards.
    """

    def __init__(self, context: "DecisionContext") -> None:
        self.context = context
        self.value: Any = _UNDECIDED

    @property
    def resolved(self) -> bool:
        """
        Whether this Decision has settled on a value. Once True, `value`
        holds the final answer and will not change.
        """
        return self.value is not _UNDECIDED

    def try_resolve(self) -> bool:
        """
        One pass of the fixed-point loop. Asks `_decide()` for an
        answer; if it returns a concrete value, commit to it and
        return True (the caller treats this as progress). If `_decide`
        returns `_UNDECIDED` — meaning dependencies aren't ready — or
        the Decision is already resolved, return False.

        Called repeatedly by `Adjudication.run` until no Decision
        makes progress in a full pass.
        """
        if self.resolved:
            return False
        result = self._decide()
        if result is _UNDECIDED:
            return False
        self.value = result
        return True

    def apply_default(self) -> None:
        """
        Commit to the fallback value from `_default()`. No-op if
        already resolved.

        Called by `Adjudication.run` once the fixed-point loop has
        stalled, to force any Decisions that never resolved to take
        their default. After this returns, every Decision in the
        context is resolved.
        """
        if self.resolved:
            return
        self.value = self._default()

    def force_resolve(self, value: Any) -> None:
        """
        Override the normal resolution flow. Used to break cycles.
        """
        self.value = value

    @abc.abstractmethod
    def _decide(self) -> Any:
        """
        Return the decided value, or _UNDECIDED if dependencies aren't ready.
        """
        ...

    @abc.abstractmethod
    def _default(self) -> Any:
        """
        Fallback value when the fixed-point loop stalls without resolution.
        """
        ...


# === Concrete Decision classes ===


class EffectiveDefenderDecision(Decision):
    """
    The unit that will be at this province after resolution.

    Value is either None (province will be empty), or an Order (the unit that
    stays — didn't move, moved illegally, or tried to move but bounced).
    """

    def __init__(self, context: "DecisionContext", province: str) -> None:
        super().__init__(context)
        self.province = province

    def _decide(self) -> Any:
        order = self.context.order_at(self.province)
        if order is None:
            return None
        if not isinstance(order, MoveOrder) or order.status == ResolutionType.ILLEGAL:
            return order
        move_decision = self.context.move_resolution.get(order)
        if move_decision is None or not move_decision.resolved:
            return _UNDECIDED
        if move_decision.value == ResolutionType.OK:
            return None
        return order

    def _default(self) -> Any:
        order = self.context.order_at(self.province)
        if order is None:
            return None
        return order


class SupportCutDecision(Decision):
    def __init__(self, context: "DecisionContext", support: SupportOrder) -> None:
        super().__init__(context)
        self.support = support

    def _decide(self) -> Any:
        attackers = self.context.attackers_into(self.support.unit.location)
        any_undecided = False
        for attacker in attackers:
            cut = self._attacker_cuts(attacker)
            if cut is True:
                return ResolutionType.CUT
            if cut is None:
                any_undecided = True
        return _UNDECIDED if any_undecided else ResolutionType.OK

    def _default(self) -> Any:
        return ResolutionType.OK

    def _attacker_cuts(self, attacker: MoveOrder) -> Optional[bool]:
        """
        Whether this attacker cuts the support. Returns True (cuts), False
        (doesn't cut), or None (cannot yet decide — convoy path pending).

        An attacker cuts unless one of these exemptions applies:
          - the attack is illegal,
          - it's from the supporter's own nation,
          - it comes from the support's cut-exception location, or
          - it's a convoyed move whose convoy path has been disrupted
            (DATC 6.F.6).
        Bouncing alone does NOT prevent the cut.
        """
        if attacker.status == ResolutionType.ILLEGAL:
            return False
        if attacker.unit.nation == self.support.unit.nation:
            return False
        cut_exception = self.support.cut_exception_location()
        if cut_exception is not None and self.context.variant.parent_of(
            attacker.unit.location
        ) == self.context.variant.parent_of(cut_exception):
            return False
        if attacker.requires_convoy:
            path_dec = self.context.convoy_path.get(attacker)
            if path_dec is None or not path_dec.resolved:
                return None
            if path_dec.value is False:
                return False
        return True


class AttackStrengthDecision(Decision):
    def __init__(self, context: "DecisionContext", move: MoveOrder) -> None:
        super().__init__(context)
        self.move = move

    def _decide(self) -> Any:
        if self.move.requires_convoy:
            path_dec = self.context.convoy_path.get(self.move)
            if path_dec is None or not path_dec.resolved:
                return _UNDECIDED
            if path_dec.value is False:
                return 0
        defender_nation = self._defender_nation()
        if defender_nation is _UNDECIDED:
            # The defender's nation is only relevant for two checks:
            #   1. Same-nation attack (returns 0)
            #   2. Dropping supports from the defender's nation
            # If neither of those can fire regardless of the eventual
            # defender, we can still resolve the attack strength.
            possible = self._possible_defender_nations()
            if self.move.unit.nation in possible:
                return _UNDECIDED
            supports = self.context.attack_supports_of(self.move)
            if any(s.unit.nation in possible for s in supports):
                return _UNDECIDED
            defender_nation = None
        if defender_nation == self.move.unit.nation:
            return 0
        supports = self.context.attack_supports_of(self.move)
        if not all(self.context.support_determined(s, defender_nation) for s in supports):
            return _UNDECIDED
        active = sum(1 for s in supports if self.context.support_active(s, defender_nation))
        return 1 + active

    def _default(self) -> Any:
        defender_nation = self._defender_nation(optimistic=True)
        if defender_nation == self.move.unit.nation:
            return 0
        supports = self.context.attack_supports_of(self.move)
        active = sum(1 for s in supports if self.context.support_active(s, defender_nation))
        return 1 + active

    def _defender_nation(self, optimistic: bool = False) -> Any:
        """
        The effective defender's nation, None for empty, or _UNDECIDED.
        If `optimistic`, assumes 'defender stays' when undecided rather
        than returning _UNDECIDED.
        """
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            return h2h.unit.nation
        defender_dec = self.context.effective_defender_at(self.move.target)
        if defender_dec is not None and defender_dec.resolved:
            defender = defender_dec.value
            return defender.unit.nation if defender is not None else None
        if not optimistic:
            return _UNDECIDED
        order = self.context.order_at(self.move.target)
        return order.unit.nation if order is not None else None

    def _possible_defender_nations(self) -> set:
        """Nations that could be the defender at the target after resolution."""
        nations: set = set()
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            nations.add(h2h.unit.nation)
        target_order = self.context.order_at(self.move.target)
        if target_order is not None:
            nations.add(target_order.unit.nation)
        return nations


class DefendStrengthDecision(Decision):
    def __init__(self, context: "DecisionContext", move: MoveOrder) -> None:
        super().__init__(context)
        self.move = move

    def _decide(self) -> Any:
        supports = self.context.attack_supports_of(self.move)
        if not all(self.context.support_determined(s) for s in supports):
            return _UNDECIDED
        return self._strength(supports)

    def _default(self) -> Any:
        return self._strength(self.context.attack_supports_of(self.move))

    def _strength(self, supports: List[SupportOrder]) -> int:
        return 1 + sum(1 for s in supports if self.context.support_active(s))


class HoldStrengthDecision(Decision):
    def __init__(self, context: "DecisionContext", province: str) -> None:
        super().__init__(context)
        self.province = province

    def _decide(self) -> Any:
        order = self.context.order_at(self.province)
        if order is None:
            return 1
        if isinstance(order, MoveOrder) and order.status != ResolutionType.ILLEGAL:
            move_dec = self.context.move_resolution.get(order)
            if move_dec is None or not move_dec.resolved:
                return _UNDECIDED
            if move_dec.value == ResolutionType.OK:
                return 0
        supports = self.context.hold_supports_of(order)
        if not all(self.context.support_determined(s) for s in supports):
            return _UNDECIDED
        return self._strength(supports)

    def _default(self) -> Any:
        order = self.context.order_at(self.province)
        if order is None:
            return 1
        if isinstance(order, MoveOrder) and order.status != ResolutionType.ILLEGAL:
            move_dec = self.context.move_resolution.get(order)
            if move_dec is not None and move_dec.value == ResolutionType.OK:
                return 0
        return self._strength(self.context.hold_supports_of(order))

    def _strength(self, supports: List[SupportOrder]) -> int:
        return 1 + sum(1 for s in supports if self.context.support_active(s))


class PreventStrengthDecision(Decision):
    def __init__(self, context: "DecisionContext", move: MoveOrder) -> None:
        super().__init__(context)
        self.move = move

    def _decide(self) -> Any:
        if self.move.requires_convoy:
            path_dec = self.context.convoy_path.get(self.move)
            if path_dec is None or not path_dec.resolved:
                return _UNDECIDED
            if path_dec.value is False:
                return 0
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            h2h_dec = self.context.move_resolution.get(h2h)
            if h2h_dec is not None and h2h_dec.value == ResolutionType.OK:
                return 0
            if h2h_dec is None or not h2h_dec.resolved:
                return _UNDECIDED
        supports = self.context.attack_supports_of(self.move)
        if not all(self.context.support_determined(s) for s in supports):
            return _UNDECIDED
        return self._strength(supports)

    def _default(self) -> Any:
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            h2h_dec = self.context.move_resolution.get(h2h)
            if h2h_dec is not None and h2h_dec.value == ResolutionType.OK:
                return 0
        return self._strength(self.context.attack_supports_of(self.move))

    def _strength(self, supports: List[SupportOrder]) -> int:
        return 1 + sum(1 for s in supports if self.context.support_active(s))


class DislodgementDecision(Decision):
    def __init__(self, context: "DecisionContext", province: str) -> None:
        super().__init__(context)
        self.province = province

    def _decide(self) -> Any:
        defender_dec = self.context.effective_defender_at(self.province)
        if defender_dec is None or not defender_dec.resolved:
            return _UNDECIDED
        if defender_dec.value is None:
            return False
        attackers = self.context.attackers_into(self.province)
        for attacker in attackers:
            move_dec = self.context.move_resolution.get(attacker)
            if move_dec is not None and move_dec.value == ResolutionType.OK:
                return True
        if all(self._attacker_cannot_succeed(a) for a in attackers):
            return False
        return _UNDECIDED

    def _default(self) -> Any:
        return False

    def _attacker_cannot_succeed(self, attacker: MoveOrder) -> bool:
        # attackers_into filters out ILLEGAL, so the only way an attacker
        # in this list can fail is by bouncing.
        move_dec = self.context.move_resolution.get(attacker)
        return move_dec is not None and move_dec.value == ResolutionType.BOUNCE


class ConvoyPathDecision(Decision):
    """
    Whether a convoyed Move has a working chain of non-dislodged
    convoying fleets connecting its source to its destination.

    Defaults to False — when the fixed-point loop stalls, any
    unresolved convoy path is treated as broken (Szykman rule). This
    resolves convoy paradoxes by collapsing the cycle to "convoy fails,
    army stays put".
    """

    def __init__(self, context: "DecisionContext", move: MoveOrder) -> None:
        super().__init__(context)
        self.move = move

    def _decide(self) -> Any:
        finder = self.context.convoy_path_finder
        candidates = finder._candidates(self.move.unit.location, self.move.target)
        known_dislodged: set = set()
        unknown: set = set()
        for fleet_loc in candidates:
            dis_dec = self.context.dislodgement.get(fleet_loc)
            if dis_dec is None or not dis_dec.resolved:
                unknown.add(fleet_loc)
            elif dis_dec.value is True:
                known_dislodged.add(fleet_loc)
        # Definitely no path: even treating unknowns optimistically as
        # alive, no chain works.
        if not finder.path_exists(
            self.move.unit.location, self.move.target, excluded=known_dislodged
        ):
            return False
        # Definitely yes: even treating unknowns pessimistically as
        # dislodged, a chain still works.
        if finder.path_exists(
            self.move.unit.location,
            self.move.target,
            excluded=known_dislodged | unknown,
        ):
            return True
        return _UNDECIDED

    def _default(self) -> Any:
        return False


class MoveResolutionDecision(Decision):
    def __init__(self, context: "DecisionContext", move: MoveOrder) -> None:
        super().__init__(context)
        self.move = move

    def _decide(self) -> Any:
        if self.move.requires_convoy:
            path_dec = self.context.convoy_path.get(self.move)
            if path_dec is None or not path_dec.resolved:
                return _UNDECIDED
            if path_dec.value is False:
                return ResolutionType.BOUNCE
        attack_dec = self.context.attack_strength.get(self.move)
        if attack_dec is None or not attack_dec.resolved:
            return _UNDECIDED
        attack = attack_dec.value
        if attack == 0:
            return ResolutionType.BOUNCE

        max_prevent = self._max_prevent_strength()
        if max_prevent is _UNDECIDED:
            return _UNDECIDED
        if attack <= max_prevent:
            return ResolutionType.BOUNCE

        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            return self._resolve_head_to_head(attack, h2h)
        return self._resolve_against_target(attack)

    def _default(self) -> Any:
        return ResolutionType.BOUNCE

    def _max_prevent_strength(self) -> Any:
        max_val = 0
        for other in self.context.attackers_into(self.move.target):
            if other is self.move:
                continue
            prev_dec = self.context.prevent_strength.get(other)
            if prev_dec is None or not prev_dec.resolved:
                return _UNDECIDED
            if prev_dec.value > max_val:
                max_val = prev_dec.value
        return max_val

    def _resolve_head_to_head(self, attack: int, h2h: MoveOrder) -> Any:
        defend_dec = self.context.defend_strength.get(h2h)
        if defend_dec is None or not defend_dec.resolved:
            return _UNDECIDED
        if attack <= defend_dec.value:
            return ResolutionType.BOUNCE
        return ResolutionType.OK

    def _resolve_against_target(self, attack: int) -> Any:
        defender_dec = self.context.effective_defender_at(self.move.target)
        if defender_dec is None or not defender_dec.resolved:
            return _UNDECIDED
        if defender_dec.value is None:
            return ResolutionType.OK
        hold_dec = self.context.hold_strength_at(self.move.target)
        if hold_dec is None or not hold_dec.resolved:
            return _UNDECIDED
        if attack <= hold_dec.value:
            return ResolutionType.BOUNCE
        return ResolutionType.OK


# === DecisionContext ===


class DecisionContext:
    def __init__(self, state: State, variant: Variant) -> None:
        self.state = state
        self.variant = variant
        self.units: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        self.orders: Dict[str, Order] = self._parse_orders()
        self.orders_by_parent: Dict[str, Order] = {
            variant.parent_of(loc): order for loc, order in self.orders.items()
        }
        self.convoy_path_finder = ConvoyPathFinder(self.variant, self.orders)

        # Province-keyed decisions are keyed by the parent province id —
        # a unit at "spa/nc" occupies the parent province "spa", so attacks
        # on either coast of Spain target the same defender, hold strength,
        # and dislodgement decision.
        self.effective_defender: Dict[str, EffectiveDefenderDecision] = {}
        self.attack_strength: Dict[MoveOrder, AttackStrengthDecision] = {}
        self.defend_strength: Dict[MoveOrder, DefendStrengthDecision] = {}
        self.hold_strength: Dict[str, HoldStrengthDecision] = {}
        self.prevent_strength: Dict[MoveOrder, PreventStrengthDecision] = {}
        self.support_cut: Dict[SupportOrder, SupportCutDecision] = {}
        self.move_resolution: Dict[MoveOrder, MoveResolutionDecision] = {}
        self.dislodgement: Dict[str, DislodgementDecision] = {}
        self.convoy_path: Dict[MoveOrder, ConvoyPathDecision] = {}

        self._build_decisions()

    def order_at(self, location: str) -> Optional[Order]:
        return self.orders_by_parent.get(self.variant.parent_of(location))

    def effective_defender_at(self, location: str) -> Optional[EffectiveDefenderDecision]:
        return self.effective_defender.get(self.variant.parent_of(location))

    def hold_strength_at(self, location: str) -> Optional[HoldStrengthDecision]:
        return self.hold_strength.get(self.variant.parent_of(location))

    def dislodgement_at(self, location: str) -> Optional[DislodgementDecision]:
        return self.dislodgement.get(self.variant.parent_of(location))

    def _parse_orders(self) -> Dict[str, Order]:
        orders = self._build_initial_orders()
        self._normalize_coastal_targets(orders)
        self._validate_convoys(orders)
        self._mark_redundant_convoys_illegal(orders)
        self._set_convoy_requirements(orders)
        self._validate_non_convoys(orders)
        return orders

    def _normalize_coastal_targets(self, orders: Dict[str, Order]) -> None:
        """
        Apply DATC 6.B.2 and 6.B.12: an army's named-coast target collapses
        to the parent province, and a fleet's parent-province target
        resolves to the only reachable named coast (if exactly one).
        """
        for order in orders.values():
            if not isinstance(order, MoveOrder):
                continue
            unit = order.unit
            target = order.target
            if unit.type == Unit.ARMY:
                if target in self.variant.named_coasts:
                    order.target = self.variant.named_coasts[target].parent_province
                continue
            if unit.type == Unit.FLEET and target in self.variant.provinces:
                coasts = self.variant.coasts_of(target)
                if not coasts:
                    continue
                reachable = [
                    c for c in coasts
                    if self.variant.can_move(unit.location, c, Unit.FLEET)
                ]
                if len(reachable) == 1:
                    order.target = reachable[0]

    def _build_initial_orders(self) -> Dict[str, Order]:
        orders: Dict[str, Order] = {}
        for raw in self.state.orders:
            unit = _unit_for_source(self.variant, self.units, raw.source)
            if unit is None or unit.nation != raw.nation:
                continue
            if unit.location in orders:
                continue
            try:
                parsed = Order.from_wire(
                    raw.order_type,
                    unit,
                    raw.target,
                    raw.aux,
                    raw.unit_type,
                    raw.via_convoy,
                )
            except ValueError:
                continue
            orders[unit.location] = parsed
        for unit in self.units.values():
            if unit.location not in orders:
                orders[unit.location] = HoldOrder(unit)
        return orders

    def _validate_convoys(self, orders: Dict[str, Order]) -> None:
        """Syntactic convoy validation (independent of other orders)."""
        for order in orders.values():
            if isinstance(order, ConvoyOrder):
                self._validate(order, orders)

    def _mark_redundant_convoys_illegal(self, orders: Dict[str, Order]) -> None:
        """
        Mark convoys that aren't on any minimal chain as illegal
        (DATC 6.G.7, 6.G.19). A convoy fleet is redundant if a chain
        exists for the same (army_source, target) without it.
        """
        finder = ConvoyPathFinder(self.variant, orders)
        for order in orders.values():
            if not isinstance(order, ConvoyOrder):
                continue
            if order.status == ResolutionType.ILLEGAL:
                continue
            if not finder.is_on_minimal_chain(
                order.unit.location, order.army_source, order.target
            ):
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = (
                    "Convoy fleet is not necessary for any convoy route."
                )

    def _set_convoy_requirements(self, orders: Dict[str, Order]) -> None:
        """Determine requires_convoy for Move orders."""
        finder = ConvoyPathFinder(self.variant, orders)
        for order in orders.values():
            if isinstance(order, MoveOrder):
                order.set_convoy_info(self.variant, finder)

    def _validate_non_convoys(self, orders: Dict[str, Order]) -> None:
        for order in orders.values():
            if not isinstance(order, ConvoyOrder):
                self._validate(order, orders)

    def _validate(self, order: Order, orders: Dict[str, Order]) -> None:
        failure = order.validate(self.variant, self.units, orders)
        if failure is not None:
            order.status = ResolutionType.ILLEGAL
            order.failure_reason = failure.MESSAGE

    def _build_decisions(self) -> None:
        for order in self.orders.values():
            if isinstance(order, MoveOrder) and order.status != ResolutionType.ILLEGAL:
                self.attack_strength[order] = AttackStrengthDecision(self, order)
                self.prevent_strength[order] = PreventStrengthDecision(self, order)
                self.move_resolution[order] = MoveResolutionDecision(self, order)
                if order.requires_convoy:
                    self.convoy_path[order] = ConvoyPathDecision(self, order)
                h2h = self.head_to_head_opponent(order)
                if h2h is not None and h2h not in self.defend_strength:
                    self.defend_strength[h2h] = DefendStrengthDecision(self, h2h)
            elif isinstance(order, SupportOrder) and order.status != ResolutionType.ILLEGAL:
                self.support_cut[order] = SupportCutDecision(self, order)
        for unit in self.units.values():
            parent = self.variant.parent_of(unit.location)
            if parent not in self.effective_defender:
                self.effective_defender[parent] = EffectiveDefenderDecision(self, parent)
                self.hold_strength[parent] = HoldStrengthDecision(self, parent)
                self.dislodgement[parent] = DislodgementDecision(self, parent)
        # Effective-defender decisions are also needed for move targets that
        # don't currently hold a unit (attacks into empty provinces).
        for order in self.orders.values():
            if isinstance(order, MoveOrder) and order.status != ResolutionType.ILLEGAL:
                parent = self.variant.parent_of(order.target)
                if parent not in self.effective_defender:
                    self.effective_defender[parent] = EffectiveDefenderDecision(
                        self, parent
                    )

    def attackers_into(self, location: str) -> List[MoveOrder]:
        parent = self.variant.parent_of(location)
        return [
            o
            for o in self.orders.values()
            if isinstance(o, MoveOrder)
            and self.variant.parent_of(o.target) == parent
            and o.status != ResolutionType.ILLEGAL
        ]

    def attack_supports_of(self, move: MoveOrder) -> List[SupportMoveOrder]:
        return [
            o
            for o in self.orders.values()
            if isinstance(o, SupportMoveOrder)
            and o.status != ResolutionType.ILLEGAL
            and self._support_target_matches(o.target, move.target)
            and self._support_source_matches(o.supported_source, move.unit.location)
        ]

    def hold_supports_of(self, order: Order) -> List[SupportHoldOrder]:
        results: List[SupportHoldOrder] = []
        for o in self.orders.values():
            if not isinstance(o, SupportHoldOrder):
                continue
            if o.status == ResolutionType.ILLEGAL:
                continue
            if not self._support_source_matches(o.supported_source, order.unit.location):
                continue
            if not self.support_matches(o):
                continue
            results.append(o)
        return results

    def _support_target_matches(self, support_target: str, actual_target: str) -> bool:
        if support_target == actual_target:
            return True
        return support_target == self.variant.parent_of(actual_target)

    def _support_source_matches(self, support_source: str, actual_location: str) -> bool:
        if support_source == actual_location:
            return True
        return support_source == self.variant.parent_of(actual_location)

    def support_active(
        self, s: SupportOrder, defender_nation: Optional[str] = None
    ) -> bool:
        """
        Whether this support contributes strength right now.
        """
        if s.status == ResolutionType.ILLEGAL:
            return False
        cut_dec = self.support_cut.get(s)
        if cut_dec is not None and cut_dec.value == ResolutionType.CUT:
            return False
        dis_dec = self.dislodgement_at(s.unit.location)
        if dis_dec is not None and dis_dec.value is True:
            return False
        if defender_nation is not None and s.unit.nation == defender_nation:
            return False
        return True

    def support_determined(
        self, s: SupportOrder, defender_nation: Optional[str] = None
    ) -> bool:
        """
        Whether support_active can return a final answer right now.
        """
        if s.status == ResolutionType.ILLEGAL:
            return True
        if defender_nation is not None and s.unit.nation == defender_nation:
            return True
        cut_dec = self.support_cut.get(s)
        if cut_dec is None or not cut_dec.resolved:
            return False
        dis_dec = self.dislodgement_at(s.unit.location)
        if dis_dec is None or not dis_dec.resolved:
            return False
        return True

    def support_matches(self, s: SupportOrder) -> bool:
        """
        Whether the supported unit is doing what this support claims.

        Hold supports: matched if the supported unit exists and was not
        ordered to a non-illegal Move (DATC 6.D.7, 6.D.8, 6.D.28).

        Move supports: matched if the supported unit is a non-illegal
        MoveOrder targeting the same destination this support claims.

        Coast specifications: a support that names the parent province
        matches a supported order specifying a named coast of that same
        province (DATC 6.B.7, 6.B.8, 6.B.15). A support naming a named
        coast must match the supported order exactly by parent.
        """
        supported = self.order_at(s.supported_source)
        if isinstance(s, SupportHoldOrder):
            if supported is None:
                return False
            if isinstance(supported, MoveOrder) and supported.status != ResolutionType.ILLEGAL:
                return False
            return True
        if isinstance(s, SupportMoveOrder):
            if supported is None or not isinstance(supported, MoveOrder):
                return False
            if supported.status == ResolutionType.ILLEGAL:
                return False
            if s.target == supported.target:
                return True
            return s.target == self.variant.parent_of(supported.target)
        raise TypeError(f"Unknown SupportOrder subclass: {type(s).__name__}")

    def head_to_head_opponent(self, move: MoveOrder) -> Optional[MoveOrder]:
        candidate = self.order_at(move.target)
        if candidate is None:
            return None
        if not isinstance(candidate, MoveOrder):
            return None
        if candidate.status == ResolutionType.ILLEGAL:
            return None
        if self.variant.parent_of(candidate.target) != self.variant.parent_of(move.unit.location):
            return None
        # A convoyed move is not a head-to-head — the army goes around the
        # opposing unit by sea, so the two never directly contend.
        if move.requires_convoy or candidate.requires_convoy:
            return None
        return candidate

    def all_decisions(self) -> Iterable[Decision]:
        yield from self.support_cut.values()
        yield from self.effective_defender.values()
        yield from self.attack_strength.values()
        yield from self.defend_strength.values()
        yield from self.prevent_strength.values()
        yield from self.hold_strength.values()
        yield from self.convoy_path.values()
        yield from self.move_resolution.values()
        yield from self.dislodgement.values()


# === Adjudication coordinator ===


class Adjudication:
    MAX_ITERATIONS = 200

    def __init__(self, state: State, variant: Variant) -> None:
        self.context = DecisionContext(state, variant)

    def run(self) -> None:
        self._propagate()
        self._resolve_cycles()
        self._propagate()
        self._apply_szykman_default()
        self._propagate()
        for d in self.context.all_decisions():
            d.apply_default()
        self._finalize_statuses()

    def _apply_szykman_default(self) -> None:
        """
        Szykman rule: any convoy path that the fixed-point loop can't
        decide is treated as broken. This collapses convoy paradoxes
        before the rest of the decision graph defaults — letting
        downstream decisions resolve correctly with the Szykman value.
        """
        for decision in self.context.convoy_path.values():
            if not decision.resolved:
                decision.value = False

    def _propagate(self) -> None:
        for _ in range(self.MAX_ITERATIONS):
            changed = any(d.try_resolve() for d in self.context.all_decisions())
            if not changed:
                return

    def _finalize_statuses(self) -> None:
        ctx = self.context
        for order in ctx.orders.values():
            if order.status == ResolutionType.ILLEGAL:
                continue
            if isinstance(order, MoveOrder):
                move_dec = ctx.move_resolution.get(order)
                order.status = move_dec.value if move_dec is not None else ResolutionType.OK
            elif isinstance(order, SupportOrder):
                if not ctx.support_matches(order):
                    order.status = ResolutionType.CUT
                else:
                    cut_dec = ctx.support_cut.get(order)
                    order.status = (
                        cut_dec.value if cut_dec is not None else ResolutionType.CUT
                    )
            else:
                order.status = ResolutionType.OK

    def _resolve_cycles(self) -> None:
        variant = self.context.variant
        unresolved = [
            move
            for move, dec in self.context.move_resolution.items()
            if not dec.resolved
        ]
        by_source = {variant.parent_of(m.unit.location): m for m in unresolved}
        for move in unresolved:
            if self.context.move_resolution[move].resolved:
                continue
            cycle = self._trace_cycle(move, by_source)
            if cycle is not None and self._cycle_is_clean(cycle):
                for m in cycle:
                    self.context.move_resolution[m].force_resolve(ResolutionType.OK)

    def _trace_cycle(
        self, start: MoveOrder, by_source: Dict[str, MoveOrder]
    ) -> Optional[List[MoveOrder]]:
        variant = self.context.variant
        start_parent = variant.parent_of(start.unit.location)
        chain = [start]
        seen = {start_parent}
        current = start
        while True:
            nxt = by_source.get(variant.parent_of(current.target))
            if nxt is None:
                return None
            nxt_parent = variant.parent_of(nxt.unit.location)
            if nxt_parent == start_parent:
                return chain
            if nxt_parent in seen:
                return None
            chain.append(nxt)
            seen.add(nxt_parent)
            current = nxt

    def _cycle_is_clean(self, cycle: List[MoveOrder]) -> bool:
        if len(cycle) < 2:
            return False
        ctx = self.context
        for move in cycle:
            attack = 1 + sum(
                1 for s in ctx.attack_supports_of(move) if ctx.support_active(s)
            )
            for other in ctx.attackers_into(move.target):
                if other is move:
                    continue
                prevent = 1 + sum(
                    1 for s in ctx.attack_supports_of(other) if ctx.support_active(s)
                )
                if attack <= prevent:
                    return False
        return True


# === PhaseResolver base ===


class PhaseResolver(abc.ABC):
    _registry: ClassVar[Dict[str, Type["PhaseResolver"]]] = {}

    @classmethod
    def register(cls, phase_type: str):
        def decorator(subclass):
            cls._registry[phase_type] = subclass
            return subclass

        return decorator

    @classmethod
    def for_state(cls, state: State, variant: Variant) -> PhaseResolver:
        subclass = cls._registry.get(state.phase.type)
        if subclass is None:
            raise ValueError("Subclass is not registered for phase type")
        return subclass(state, variant)

    @abc.abstractmethod
    def resolve(self) -> List[State]: ...


# === MovementPhaseResolver ===


@PhaseResolver.register(Phase.MOVEMENT)
class MovementPhaseResolver(PhaseResolver):
    def __init__(self, state: State, variant: Variant) -> None:
        self.state = state
        self.variant = variant
        self.adjudication = Adjudication(state, variant)

    def resolve(self) -> List[State]:
        self.adjudication.run()
        return self._build_next_states()

    def _build_next_states(self) -> List[State]:
        ctx = self.adjudication.context
        new_units = self._compute_new_units(ctx)
        contested = self._compute_contested_provinces(ctx)
        resolutions = [
            Resolution(
                province=src, resolution=order.status, reason=order.failure_reason
            )
            for src, order in sorted(ctx.orders.items())
        ]
        resolved = self._resolved_state(new_units, resolutions, contested)
        next_phase = self._next_phase()
        if next_phase is None:
            return [resolved]
        return [resolved, self._next_state(new_units, next_phase, contested)]

    def _resolved_state(
        self,
        new_units: List[Unit],
        resolutions: List[Resolution],
        contested: Tuple[str, ...],
    ) -> State:
        return State(
            variant=self.state.variant,
            phase=self.state.phase,
            units=new_units,
            supply_centers=list(self.state.supply_centers),
            orders=list(self.state.orders),
            resolutions=resolutions,
            skipped=False,
            outcome=None,
            contested_provinces=contested,
        )

    def _next_state(
        self,
        new_units: List[Unit],
        next_phase: Phase,
        contested: Tuple[str, ...],
    ) -> State:
        next_units = [
            Unit(
                nation=u.nation,
                type=u.type,
                location=u.location,
                dislodged=u.dislodged,
                dislodged_from=u.dislodged_from,
            )
            for u in new_units
        ]
        return State(
            variant=self.state.variant,
            phase=next_phase,
            units=next_units,
            supply_centers=list(self.state.supply_centers),
            orders=[],
            resolutions=None,
            skipped=False,
            outcome=None,
            contested_provinces=contested,
        )

    def _compute_new_units(self, ctx: DecisionContext) -> List[Unit]:
        return [self._destination_unit(unit, ctx) for unit in self.state.units]

    def _destination_unit(self, unit: Unit, ctx: DecisionContext) -> Unit:
        if unit.dislodged:
            return Unit(
                nation=unit.nation,
                type=unit.type,
                location=unit.location,
                dislodged=True,
                dislodged_from=unit.dislodged_from,
            )
        order = ctx.orders.get(unit.location)
        if (
            order is not None
            and order.status == ResolutionType.OK
            and order.moves_to is not None
        ):
            return Unit(
                nation=unit.nation,
                type=unit.type,
                location=order.moves_to,
                dislodged=False,
            )
        dis_dec = ctx.dislodgement_at(unit.location)
        is_dislodged = dis_dec is not None and dis_dec.value is True
        dislodged_from = self._dislodger_origin(unit, ctx) if is_dislodged else None
        return Unit(
            nation=unit.nation,
            type=unit.type,
            location=unit.location,
            dislodged=is_dislodged,
            dislodged_from=dislodged_from,
        )

    def _dislodger_origin(self, unit: Unit, ctx: DecisionContext) -> Optional[str]:
        """
        The parent province of the attacker that dislodged this unit, or
        None if the attacker came by convoy (DATC 6.H.11). A convoyed
        attacker imposes no retreat restriction since it never crossed
        the contested border directly.
        """
        for attacker in ctx.attackers_into(unit.location):
            move_dec = ctx.move_resolution.get(attacker)
            if move_dec is None or move_dec.value != ResolutionType.OK:
                continue
            if attacker.requires_convoy:
                return None
            return self.variant.parent_of(attacker.unit.location)
        return None

    def _compute_contested_provinces(self, ctx: DecisionContext) -> Tuple[str, ...]:
        """
        Provinces where a standoff occurred: at least two non-illegal
        moves targeted the same parent province and none succeeded.
        Returned as parent province ids (DATC 6.H.6, 6.H.16).
        """
        by_parent: Dict[str, List[MoveOrder]] = {}
        for order in ctx.orders.values():
            if not isinstance(order, MoveOrder):
                continue
            if order.status == ResolutionType.ILLEGAL:
                continue
            parent = self.variant.parent_of(order.target)
            by_parent.setdefault(parent, []).append(order)
        contested: List[str] = []
        for parent, moves in by_parent.items():
            if len(moves) < 2:
                continue
            if any(
                ctx.move_resolution.get(m) is not None
                and ctx.move_resolution[m].value == ResolutionType.OK
                for m in moves
            ):
                continue
            contested.append(parent)
        return tuple(sorted(contested))

    def _next_phase(self) -> Optional[Phase]:
        for transition in self.variant.phase_progression.transitions:
            if (
                transition.from_season == self.state.phase.season
                and transition.from_type == self.state.phase.type
            ):
                return Phase(
                    season=transition.to_season,
                    year=self.state.phase.year + transition.year_delta,
                    type=transition.to_type,
                )
        return None


# === RetreatPhaseResolver ===


@PhaseResolver.register(Phase.RETREAT)
class RetreatPhaseResolver(PhaseResolver):
    """
    Resolve the Retreat phase: each dislodged unit either retreats to an
    adjacent unoccupied non-contested province or disbands. Multiple
    retreats to the same parent province all fail (DATC 6.H.7, 6.H.8).
    Only RetreatOrder and DisbandOrder are accepted; any other order
    type is rejected at parse time (DATC 6.H.1-6.H.4).
    """

    def __init__(self, state: State, variant: Variant) -> None:
        self.state = state
        self.variant = variant
        self.dislodged_units: Dict[str, Unit] = {
            u.location: u for u in state.units if u.dislodged
        }
        self.standing_units: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        self.contested = set(state.contested_provinces)
        self.orders_by_loc: Dict[str, Order] = {}

    def resolve(self) -> List[State]:
        self._parse_orders()
        self._resolve_bounces()
        return self._build_next_states()

    def _parse_orders(self) -> None:
        for raw in self.state.orders:
            unit = _unit_for_source(self.variant, self.dislodged_units, raw.source)
            if unit is None or unit.nation != raw.nation:
                continue
            if raw.order_type not in (OrderType.RETREAT, OrderType.DISBAND):
                continue
            if unit.location in self.orders_by_loc:
                continue
            try:
                parsed = Order.from_wire(
                    raw.order_type, unit, raw.target, raw.aux, raw.unit_type, raw.via_convoy
                )
            except ValueError:
                continue
            self.orders_by_loc[unit.location] = parsed
        for loc, unit in self.dislodged_units.items():
            if loc not in self.orders_by_loc:
                self.orders_by_loc[loc] = DisbandOrder(unit)
        self._apply_legality_checks()
        self._enforce_contested_targets()

    def _apply_legality_checks(self) -> None:
        for order in self.orders_by_loc.values():
            failure = order.validate(self.variant, self.standing_units, self.orders_by_loc)
            if failure is not None:
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = failure.MESSAGE

    def _enforce_contested_targets(self) -> None:
        for order in self.orders_by_loc.values():
            if not isinstance(order, RetreatOrder):
                continue
            if order.status == ResolutionType.ILLEGAL:
                continue
            if self.variant.parent_of(order.target) in self.contested:
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = "The retreat destination is contested."

    def _resolve_bounces(self) -> None:
        targets: Dict[str, List[RetreatOrder]] = {}
        for order in self.orders_by_loc.values():
            if not isinstance(order, RetreatOrder):
                continue
            if order.status == ResolutionType.ILLEGAL:
                continue
            targets.setdefault(self.variant.parent_of(order.target), []).append(order)
        for parent, contenders in targets.items():
            if len(contenders) >= 2:
                for retreat in contenders:
                    retreat.status = ResolutionType.BOUNCE
                    retreat.failure_reason = (
                        "Multiple units retreat to the same province; all disband."
                    )
        for order in self.orders_by_loc.values():
            if order.status is None:
                order.status = ResolutionType.OK

    def _build_next_states(self) -> List[State]:
        new_units = self._compute_new_units()
        resolutions = [
            Resolution(
                province=src, resolution=order.status, reason=order.failure_reason
            )
            for src, order in sorted(self.orders_by_loc.items())
        ]
        resolved = State(
            variant=self.state.variant,
            phase=self.state.phase,
            units=new_units,
            supply_centers=list(self.state.supply_centers),
            orders=list(self.state.orders),
            resolutions=resolutions,
            skipped=False,
            outcome=None,
            contested_provinces=tuple(self.state.contested_provinces),
        )
        next_phase = self._next_phase()
        if next_phase is None:
            return [resolved]
        next_units = [
            Unit(
                nation=u.nation,
                type=u.type,
                location=u.location,
                dislodged=False,
                dislodged_from=None,
            )
            for u in new_units
        ]
        next_state = State(
            variant=self.state.variant,
            phase=next_phase,
            units=next_units,
            supply_centers=list(self.state.supply_centers),
            orders=[],
            resolutions=None,
            skipped=False,
            outcome=None,
            contested_provinces=(),
        )
        return [resolved, next_state]

    def _compute_new_units(self) -> List[Unit]:
        new_units: List[Unit] = []
        for unit in self.state.units:
            if not unit.dislodged:
                new_units.append(
                    Unit(
                        nation=unit.nation,
                        type=unit.type,
                        location=unit.location,
                        dislodged=False,
                        dislodged_from=None,
                    )
                )
                continue
            order = self.orders_by_loc.get(unit.location)
            if (
                isinstance(order, RetreatOrder)
                and order.status == ResolutionType.OK
            ):
                new_units.append(
                    Unit(
                        nation=unit.nation,
                        type=unit.type,
                        location=order.target,
                        dislodged=False,
                        dislodged_from=None,
                    )
                )
        return new_units

    def _next_phase(self) -> Optional[Phase]:
        for transition in self.variant.phase_progression.transitions:
            if (
                transition.from_season == self.state.phase.season
                and transition.from_type == self.state.phase.type
            ):
                return Phase(
                    season=transition.to_season,
                    year=self.state.phase.year + transition.year_delta,
                    type=transition.to_type,
                )
        return None


# === AdjustmentPhaseResolver ===


@PhaseResolver.register(Phase.ADJUSTMENT)
class AdjustmentPhaseResolver(PhaseResolver):
    """
    Resolve the Adjustment phase. Each nation reconciles its unit count
    with its owned-supply-center count: shortfall powers build, surplus
    powers disband. Excess build / disband orders fail in the order
    submitted. Disband shortfalls are filled by civil disorder
    (DATC 6.J.3–6.J.11): remove units furthest from any owned supply
    center, with fleets preferred over armies and ties broken
    alphabetically by location id.

    Civil-disorder distance ignores pass restrictions per
    DATC 6.J.5/6.J.6 footnotes — any adjacency counts as a hop. The
    target supply centers are the nation's currently-owned ones
    (DATC 6.J.11, 2023 rules).
    """

    BUILD_TOO_MANY = "Nation has already built its allowed number of units."
    BUILD_NOT_SUPPLY_CENTER = "Build location is not a supply center."
    BUILD_NOT_OWNED = "Build location is not owned by this nation."
    BUILD_NOT_HOME = "Build location is not a home supply center for this nation."
    BUILD_OCCUPIED = "Build location is already occupied."
    BUILD_DUPLICATE_TARGET = (
        "Another build for this province has already been ordered."
    )
    BUILD_INVALID_UNIT_TYPE = "Build order has an invalid unit type."
    BUILD_FLEET_IN_LANDLOCKED = "Fleets cannot be built in landlocked provinces."
    BUILD_NEEDS_COAST = (
        "A fleet build in a multi-coast province must specify a named coast."
    )
    DISBAND_NO_SUCH_UNIT = "No unit of this nation exists at the source location."
    DISBAND_DUPLICATE = "This unit has already been ordered to disband."
    DISBAND_TOO_MANY = "Nation has already disbanded its required number of units."

    ALLOW_NON_HOME = "allow-builds-in-non-home-centers"

    def __init__(self, state: State, variant: Variant) -> None:
        self.state = state
        self.variant = variant
        self.units_by_loc: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        self.owned_by_nation: Dict[str, List[str]] = {}
        for sc in state.supply_centers:
            self.owned_by_nation.setdefault(sc.nation, []).append(sc.province)
        self.parsed_orders: List[Order] = []
        self.civil_disorder_disbands: List[Unit] = []

    def resolve(self) -> List[State]:
        self._parse_orders()
        self._resolve_orders()
        self._apply_civil_disorder()
        return self._build_next_states()

    def _parse_orders(self) -> None:
        for raw in self.state.orders:
            if raw.order_type == OrderType.BUILD:
                target = raw.target if raw.target is not None else raw.source
                order = BuildOrder(
                    nation=raw.nation,
                    location=target if target is not None else "",
                    unit_type=raw.unit_type,
                )
                self.parsed_orders.append(order)
            elif raw.order_type == OrderType.DISBAND:
                unit = _unit_for_source(
                    self.variant, self.units_by_loc, raw.source or ""
                )
                if unit is None or unit.nation != raw.nation:
                    placeholder = DisbandOrder(
                        Unit(
                            nation=raw.nation,
                            type=Unit.ARMY,
                            location=raw.source or "",
                        )
                    )
                    placeholder.status = ResolutionType.ILLEGAL
                    placeholder.failure_reason = self.DISBAND_NO_SUCH_UNIT
                    self.parsed_orders.append(placeholder)
                else:
                    self.parsed_orders.append(DisbandOrder(unit))

    def _resolve_orders(self) -> None:
        for nation in self._nations_with_orders():
            delta = self._delta_for(nation)
            if delta > 0:
                self._resolve_builds_for(nation, delta)
            elif delta < 0:
                self._resolve_disbands_for(nation, -delta)
            else:
                self._mark_no_op_orders(nation)

    def _nations_with_orders(self) -> List[str]:
        seen: List[str] = []
        for order in self.parsed_orders:
            nation = self._nation_of(order)
            if nation not in seen:
                seen.append(nation)
        return seen

    def _nation_of(self, order: Order) -> str:
        if isinstance(order, BuildOrder):
            return order.nation
        if isinstance(order, DisbandOrder) and order.unit is not None:
            return order.unit.nation
        return ""

    def _delta_for(self, nation: str) -> int:
        owned = len(self.owned_by_nation.get(nation, []))
        units = sum(1 for u in self.state.units if u.nation == nation and not u.dislodged)
        return owned - units

    def _resolve_builds_for(self, nation: str, allowed: int) -> None:
        successful_targets: set = set()
        successful_count = 0
        for order in self.parsed_orders:
            if not isinstance(order, BuildOrder) or order.nation != nation:
                continue
            if order.status is not None:
                continue
            failure = self._build_failure_reason(order, successful_targets)
            if failure is not None:
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = failure
                continue
            if successful_count >= allowed:
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = self.BUILD_TOO_MANY
                continue
            order.status = ResolutionType.OK
            successful_targets.add(self.variant.parent_of(order.location))
            successful_count += 1

    def _build_failure_reason(
        self, order: BuildOrder, successful_targets: set
    ) -> Optional[str]:
        if order.unit_type not in (Unit.ARMY, Unit.FLEET):
            return self.BUILD_INVALID_UNIT_TYPE
        if order.location not in self.variant.provinces and order.location not in self.variant.named_coasts:
            return self.BUILD_NOT_SUPPLY_CENTER
        parent = self.variant.parent_of(order.location)
        province = self.variant.provinces.get(parent)
        if province is None or not province.supply_center:
            return self.BUILD_NOT_SUPPLY_CENTER
        owned = set(self.owned_by_nation.get(order.nation, []))
        if parent not in owned:
            return self.BUILD_NOT_OWNED
        if (
            self.ALLOW_NON_HOME not in self.variant.adjudication_modifiers
            and province.home_nation != order.nation
        ):
            return self.BUILD_NOT_HOME
        if self._province_occupied(parent):
            return self.BUILD_OCCUPIED
        if parent in successful_targets:
            return self.BUILD_DUPLICATE_TARGET
        if order.unit_type == Unit.FLEET:
            if order.location == parent:
                if self.variant.coasts_of(parent):
                    return self.BUILD_NEEDS_COAST
                if not self.variant.has_fleet_access(parent):
                    return self.BUILD_FLEET_IN_LANDLOCKED
            else:
                if order.location not in self.variant.named_coasts:
                    return self.BUILD_FLEET_IN_LANDLOCKED
        else:
            if order.location in self.variant.named_coasts:
                return self.BUILD_INVALID_UNIT_TYPE
        return None

    def _province_occupied(self, parent: str) -> bool:
        for unit in self.units_by_loc.values():
            if self.variant.parent_of(unit.location) == parent:
                return True
        return False

    def _resolve_disbands_for(self, nation: str, required: int) -> None:
        successful_locations: set = set()
        successful_count = 0
        for order in self.parsed_orders:
            if not isinstance(order, DisbandOrder):
                continue
            if order.unit is None or order.unit.nation != nation:
                continue
            if order.status == ResolutionType.ILLEGAL:
                continue
            if order.status is not None:
                continue
            parent = self.variant.parent_of(order.unit.location)
            if parent in successful_locations:
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = self.DISBAND_DUPLICATE
                continue
            if successful_count >= required:
                order.status = ResolutionType.ILLEGAL
                order.failure_reason = self.DISBAND_TOO_MANY
                continue
            order.status = ResolutionType.OK
            successful_locations.add(parent)
            successful_count += 1

    def _apply_civil_disorder(self) -> None:
        for nation in self._all_nations():
            delta = self._delta_for(nation)
            if delta >= 0:
                continue
            required = -delta
            already_disbanded = self._disbanded_parents(nation)
            if len(already_disbanded) >= required:
                continue
            shortfall = required - len(already_disbanded)
            remaining = [
                u
                for u in self.state.units
                if u.nation == nation
                and not u.dislodged
                and self.variant.parent_of(u.location) not in already_disbanded
            ]
            ranked = self._rank_for_civil_disorder(nation, remaining)
            for unit in ranked[:shortfall]:
                self.civil_disorder_disbands.append(unit)

    def _all_nations(self) -> List[str]:
        seen: List[str] = []
        for n in self.owned_by_nation:
            if n not in seen:
                seen.append(n)
        for u in self.state.units:
            if u.nation not in seen:
                seen.append(u.nation)
        return seen

    def _disbanded_parents(self, nation: str) -> set:
        return {
            self.variant.parent_of(o.unit.location)
            for o in self.parsed_orders
            if isinstance(o, DisbandOrder)
            and o.unit is not None
            and o.unit.nation == nation
            and o.status == ResolutionType.OK
        }

    def _rank_for_civil_disorder(
        self, nation: str, units: List[Unit]
    ) -> List[Unit]:
        owned = self.owned_by_nation.get(nation, [])
        distances = {
            id(unit): self._distance_to_owned(unit.location, owned)
            for unit in units
        }
        return sorted(
            units,
            key=lambda u: (
                -distances[id(u)],
                0 if u.type == Unit.FLEET else 1,
                u.location,
            ),
        )

    def _distance_to_owned(self, start: str, owned: List[str]) -> int:
        if not owned:
            return 0
        target_set = set()
        for province_id in owned:
            target_set.add(province_id)
            for coast in self.variant.coasts_of(province_id):
                target_set.add(coast)
        if start in target_set:
            return 0
        if self.variant.parent_of(start) in {p for p in owned}:
            return 0
        visited = {start}
        frontier = {start}
        depth = 0
        while frontier:
            depth += 1
            next_frontier: set = set()
            for node in frontier:
                for adjacency in self.variant.adjacencies_of(node):
                    neighbour = adjacency.to
                    if neighbour in visited:
                        continue
                    visited.add(neighbour)
                    if neighbour in target_set:
                        return depth
                    if self.variant.parent_of(neighbour) in {p for p in owned}:
                        return depth
                    next_frontier.add(neighbour)
            frontier = next_frontier
        return depth

    def _mark_no_op_orders(self, nation: str) -> None:
        for order in self.parsed_orders:
            if self._nation_of(order) != nation:
                continue
            if order.status is not None:
                continue
            order.status = ResolutionType.ILLEGAL
            if isinstance(order, BuildOrder):
                order.failure_reason = self.BUILD_TOO_MANY
            else:
                order.failure_reason = self.DISBAND_TOO_MANY

    def _build_next_states(self) -> List[State]:
        new_units = self._compute_new_units()
        resolutions = self._compute_resolutions()
        resolved = State(
            variant=self.state.variant,
            phase=self.state.phase,
            units=new_units,
            supply_centers=list(self.state.supply_centers),
            orders=list(self.state.orders),
            resolutions=resolutions,
            skipped=False,
            outcome=None,
            contested_provinces=(),
        )
        next_phase = self._next_phase()
        if next_phase is None:
            return [resolved]
        next_units = [
            Unit(
                nation=u.nation,
                type=u.type,
                location=u.location,
                dislodged=False,
                dislodged_from=None,
            )
            for u in new_units
        ]
        next_state = State(
            variant=self.state.variant,
            phase=next_phase,
            units=next_units,
            supply_centers=list(self.state.supply_centers),
            orders=[],
            resolutions=None,
            skipped=False,
            outcome=None,
            contested_provinces=(),
        )
        return [resolved, next_state]

    def _compute_new_units(self) -> List[Unit]:
        disbanded_locations: set = {
            order.unit.location
            for order in self.parsed_orders
            if isinstance(order, DisbandOrder)
            and order.unit is not None
            and order.status == ResolutionType.OK
        }
        disbanded_locations.update(u.location for u in self.civil_disorder_disbands)
        kept: List[Unit] = []
        for unit in self.state.units:
            if unit.dislodged:
                continue
            if unit.location in disbanded_locations:
                continue
            kept.append(
                Unit(
                    nation=unit.nation,
                    type=unit.type,
                    location=unit.location,
                    dislodged=False,
                    dislodged_from=None,
                )
            )
        for order in self.parsed_orders:
            if not isinstance(order, BuildOrder):
                continue
            if order.status != ResolutionType.OK:
                continue
            kept.append(
                Unit(
                    nation=order.nation,
                    type=order.unit_type or Unit.ARMY,
                    location=order.location,
                    dislodged=False,
                    dislodged_from=None,
                )
            )
        return kept

    def _compute_resolutions(self) -> List[Resolution]:
        resolutions: List[Resolution] = []
        for order in self.parsed_orders:
            if isinstance(order, BuildOrder):
                province = order.location or ""
            elif isinstance(order, DisbandOrder) and order.unit is not None:
                province = order.unit.location
            else:
                province = ""
            resolutions.append(
                Resolution(
                    province=province,
                    resolution=order.status or ResolutionType.OK,
                    reason=order.failure_reason,
                )
            )
        return resolutions

    def _next_phase(self) -> Optional[Phase]:
        for transition in self.variant.phase_progression.transitions:
            if (
                transition.from_season == self.state.phase.season
                and transition.from_type == self.state.phase.type
            ):
                return Phase(
                    season=transition.to_season,
                    year=self.state.phase.year + transition.year_delta,
                    type=transition.to_type,
                )
        return None


# === Option enumerators ===


class HoldOptions:
    @classmethod
    def for_unit(
        cls, unit: Unit, variant: Variant, units_by_loc: Dict[str, Unit]
    ) -> List[OrderOption]:
        return [
            OrderOption(
                source=unit.location,
                order_type=OrderType.HOLD,
                target=None,
                aux=None,
                unit_type=None,
                named_coast=None,
            )
        ]


class MoveOptions:
    @classmethod
    def for_unit(
        cls, unit: Unit, variant: Variant, units_by_loc: Dict[str, Unit]
    ) -> List[OrderOption]:
        options: List[OrderOption] = []
        emitted_targets: set = set()
        for adjacency in variant.adjacencies_of(unit.location):
            if adjacency.to == unit.location:
                continue
            if not adjacency.allows(unit.type):
                continue
            emitted_targets.add(adjacency.to)
            options.append(
                OrderOption(
                    source=unit.location,
                    order_type=OrderType.MOVE,
                    target=adjacency.to,
                    aux=None,
                    unit_type=None,
                    named_coast=None,
                )
            )
        if unit.type == Unit.ARMY:
            for dest in _convoy_reachable_coasts(unit.location, variant, units_by_loc):
                if dest == unit.location or dest in emitted_targets:
                    continue
                emitted_targets.add(dest)
                options.append(
                    OrderOption(
                        source=unit.location,
                        order_type=OrderType.MOVE,
                        target=dest,
                        aux=None,
                        unit_type=None,
                        named_coast=None,
                    )
                )
        return options


class ConvoyOptions:
    @classmethod
    def for_unit(
        cls, unit: Unit, variant: Variant, units_by_loc: Dict[str, Unit]
    ) -> List[OrderOption]:
        if unit.type != Unit.FLEET:
            return []
        province = variant.provinces.get(unit.location)
        if province is None or province.type != ProvinceType.SEA:
            return []
        component = _sea_fleet_component(unit.location, variant, units_by_loc)
        if not component:
            return []
        coasts = _coasts_touching(component, variant)
        options: List[OrderOption] = []
        for army_loc in coasts:
            army = units_by_loc.get(army_loc)
            if army is None or army.type != Unit.ARMY:
                continue
            for dest in coasts:
                if dest == army_loc:
                    continue
                options.append(
                    OrderOption(
                        source=unit.location,
                        order_type=OrderType.CONVOY,
                        target=dest,
                        aux=army_loc,
                        unit_type=None,
                        named_coast=None,
                    )
                )
        return options


def _sea_fleets_by_loc(
    variant: Variant, units_by_loc: Dict[str, Unit]
) -> set:
    return {
        u.location
        for u in units_by_loc.values()
        if u.type == Unit.FLEET
        and variant.provinces.get(u.location) is not None
        and variant.provinces[u.location].type == ProvinceType.SEA
    }


def _sea_fleet_component(
    start_sea: str, variant: Variant, units_by_loc: Dict[str, Unit]
) -> set:
    sea_fleets = _sea_fleets_by_loc(variant, units_by_loc)
    if start_sea not in sea_fleets:
        return set()
    component = {start_sea}
    frontier = {start_sea}
    while frontier:
        new_frontier: set = set()
        for sea in frontier:
            for adjacency in variant.adjacencies_of(sea):
                if not adjacency.allows(Unit.FLEET):
                    continue
                if adjacency.to in sea_fleets and adjacency.to not in component:
                    new_frontier.add(adjacency.to)
        component.update(new_frontier)
        frontier = new_frontier
    return component


def _coasts_touching(component: set, variant: Variant) -> set:
    coasts: set = set()
    for sea in component:
        for adjacency in variant.adjacencies_of(sea):
            if not adjacency.allows(Unit.FLEET):
                continue
            target_id = adjacency.to
            named = variant.named_coasts.get(target_id)
            if named is not None:
                target_id = named.parent_province
            target_prov = variant.provinces.get(target_id)
            if target_prov is None:
                continue
            if target_prov.type != ProvinceType.SEA:
                coasts.add(target_id)
    return coasts


def _convoy_reachable_coasts(
    army_source: str, variant: Variant, units_by_loc: Dict[str, Unit]
) -> set:
    sea_fleets = _sea_fleets_by_loc(variant, units_by_loc)
    start_seas = {
        adjacency.to
        for adjacency in variant.adjacencies_of(army_source)
        if adjacency.allows(Unit.FLEET) and adjacency.to in sea_fleets
    }
    component: set = set()
    for sea in start_seas:
        component |= _sea_fleet_component(sea, variant, units_by_loc)
    return _coasts_touching(component, variant)


class SupportOptions:
    @classmethod
    def for_unit(
        cls, unit: Unit, variant: Variant, units_by_loc: Dict[str, Unit]
    ) -> List[OrderOption]:
        options: List[OrderOption] = []
        reachable = [
            adjacency.to
            for adjacency in variant.adjacencies_of(unit.location)
            if adjacency.to != unit.location and adjacency.allows(unit.type)
        ]
        for target in reachable:
            for other_loc, other_unit in units_by_loc.items():
                if other_loc == unit.location:
                    continue
                if other_loc == target:
                    options.append(
                        OrderOption(
                            source=unit.location,
                            order_type=OrderType.SUPPORT,
                            target=target,
                            aux=target,
                            unit_type=None,
                            named_coast=None,
                        )
                    )
                elif variant.can_move(other_loc, target, other_unit.type):
                    options.append(
                        OrderOption(
                            source=unit.location,
                            order_type=OrderType.SUPPORT,
                            target=target,
                            aux=other_loc,
                            unit_type=None,
                            named_coast=None,
                        )
                    )
        return options


class RetreatOptions:
    @classmethod
    def for_dislodged(
        cls,
        unit: Unit,
        variant: Variant,
        standing_by_loc: Dict[str, Unit],
        contested: set,
    ) -> List[OrderOption]:
        options: List[OrderOption] = [
            OrderOption(
                source=unit.location,
                order_type=OrderType.DISBAND,
                target=None,
                aux=None,
                unit_type=None,
                named_coast=None,
            )
        ]
        for adjacency in variant.adjacencies_of(unit.location):
            if not adjacency.allows(unit.type):
                continue
            target = adjacency.to
            target_parent = variant.parent_of(target)
            if target_parent in contested:
                continue
            if any(
                variant.parent_of(loc) == target_parent for loc in standing_by_loc
            ):
                continue
            if (
                unit.dislodged_from is not None
                and variant.parent_of(unit.dislodged_from) == target_parent
            ):
                continue
            options.append(
                OrderOption(
                    source=unit.location,
                    order_type=OrderType.RETREAT,
                    target=target,
                    aux=None,
                    unit_type=None,
                    named_coast=None,
                )
            )
        return options


# === Adjustment-phase option enumerators ===


class BuildOptions:
    @classmethod
    def for_nation(
        cls,
        nation: str,
        variant: Variant,
        units_by_loc: Dict[str, Unit],
        owned_scs: List[str],
    ) -> List[OrderOption]:
        options: List[OrderOption] = []
        allow_non_home = (
            AdjustmentPhaseResolver.ALLOW_NON_HOME in variant.adjudication_modifiers
        )
        occupied_parents = {
            variant.parent_of(loc) for loc in units_by_loc
        }
        for sc in owned_scs:
            province = variant.provinces.get(sc)
            if province is None or not province.supply_center:
                continue
            if not allow_non_home and province.home_nation != nation:
                continue
            if sc in occupied_parents:
                continue
            if province.type != ProvinceType.SEA:
                options.append(
                    OrderOption(
                        source=None,
                        order_type=OrderType.BUILD,
                        target=sc,
                        aux=None,
                        unit_type=Unit.ARMY,
                        named_coast=None,
                    )
                )
            coasts = variant.coasts_of(sc)
            if coasts:
                for coast in coasts:
                    options.append(
                        OrderOption(
                            source=None,
                            order_type=OrderType.BUILD,
                            target=coast,
                            aux=None,
                            unit_type=Unit.FLEET,
                            named_coast=None,
                        )
                    )
            elif variant.has_fleet_access(sc):
                options.append(
                    OrderOption(
                        source=None,
                        order_type=OrderType.BUILD,
                        target=sc,
                        aux=None,
                        unit_type=Unit.FLEET,
                        named_coast=None,
                    )
                )
        return options


class DisbandOptions:
    @classmethod
    def for_unit(cls, unit: Unit) -> List[OrderOption]:
        return [
            OrderOption(
                source=unit.location,
                order_type=OrderType.DISBAND,
                target=None,
                aux=None,
                unit_type=None,
                named_coast=None,
            )
        ]


# === OptionsBuilder ===


class OptionsBuilder:
    _MOVEMENT_ENUMERATORS: Tuple[type, ...] = (
        HoldOptions, MoveOptions, SupportOptions, ConvoyOptions,
    )

    def __init__(self, variant: Variant) -> None:
        self.variant = variant

    def build(self, state: State) -> List[OrderOption]:
        if state.phase.type == Phase.MOVEMENT:
            return self._movement_options(state)
        if state.phase.type == Phase.RETREAT:
            return self._retreat_options(state)
        if state.phase.type == Phase.ADJUSTMENT:
            return self._adjustment_options(state)
        return []

    def _movement_options(self, state: State) -> List[OrderOption]:
        units_by_loc: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        return [
            option
            for unit in state.units
            if not unit.dislodged
            for enumerator in self._MOVEMENT_ENUMERATORS
            for option in enumerator.for_unit(unit, self.variant, units_by_loc)
        ]

    def _retreat_options(self, state: State) -> List[OrderOption]:
        standing_by_loc: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        contested = set(state.contested_provinces)
        return [
            option
            for unit in state.units
            if unit.dislodged
            for option in RetreatOptions.for_dislodged(
                unit, self.variant, standing_by_loc, contested
            )
        ]

    def _adjustment_options(self, state: State) -> List[OrderOption]:
        units_by_loc: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        owned_by_nation: Dict[str, List[str]] = {}
        for sc in state.supply_centers:
            owned_by_nation.setdefault(sc.nation, []).append(sc.province)
        options: List[OrderOption] = []
        for nation in self._nations_in_state(state):
            owned = len(owned_by_nation.get(nation, []))
            units = sum(
                1 for u in state.units if u.nation == nation and not u.dislodged
            )
            delta = owned - units
            if delta > 0:
                options.extend(
                    BuildOptions.for_nation(
                        nation,
                        self.variant,
                        units_by_loc,
                        owned_by_nation.get(nation, []),
                    )
                )
            elif delta < 0:
                for unit in state.units:
                    if unit.dislodged or unit.nation != nation:
                        continue
                    options.extend(DisbandOptions.for_unit(unit))
        return options

    def _nations_in_state(self, state: State) -> List[str]:
        seen: List[str] = []
        for sc in state.supply_centers:
            if sc.nation not in seen:
                seen.append(sc.nation)
        for u in state.units:
            if u.nation not in seen:
                seen.append(u.nation)
        return seen
