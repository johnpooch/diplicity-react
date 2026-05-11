from __future__ import annotations

import abc
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Tuple, Type

from .domain import (
    OrderOption,
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
        Resolve the orders for a phase.

        Returns a list with two elements: the input state with `resolutions`
        populated (what just happened), and the next phase to be played
        with `resolutions=None` (where input is needed next).

        If the phase has no successor (game over), only the resolved input
        state is returned.

        TODO (Phase 7): when the next phase requires no orders (e.g. a
        Retreat phase with no dislodgements), auto-resolve it and append
        the phase after.
        """
        return PhaseResolver.for_state(state, self.variant).resolve()

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
            return True
        return False


class SupportHoldNotSelfSupport(LegalityCheck):
    MESSAGE = "A unit can't support itself."

    def passes(self, order: "SupportHoldOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return order.supported_source != order.unit.location


class SupportHoldHasSupportedUnit(LegalityCheck):
    MESSAGE = "There's no unit at the supported province."

    def passes(self, order: "SupportHoldOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return order.supported_source in units_by_loc


class SupportHoldSupporterCanReach(LegalityCheck):
    MESSAGE = "The supporting unit can't reach the supported province."

    def passes(self, order: "SupportHoldOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.can_move(
            order.unit.location, order.supported_source, order.unit.type
        )


class SupportMoveNotIntoSelf(LegalityCheck):
    MESSAGE = "A unit can't support an attack into its own province."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return order.target != order.unit.location


class SupportMoveSupporterCanReach(LegalityCheck):
    MESSAGE = "The supporting unit can't reach the target."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return variant.can_move(order.unit.location, order.target, order.unit.type)


class SupportMoveHasSupportedUnit(LegalityCheck):
    MESSAGE = "There's no unit at the supported source province."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        return order.supported_source in units_by_loc


class SupportMoveSupportedCanReach(LegalityCheck):
    MESSAGE = "The supported unit can't itself reach the target."

    def passes(self, order: "SupportMoveOrder", variant, units_by_loc, orders_by_loc) -> bool:
        supported = units_by_loc.get(order.supported_source)
        if supported is None:
            return True
        if variant.can_move(order.supported_source, order.target, supported.type):
            return True
        if supported.type == Unit.ARMY:
            finder = ConvoyPathFinder(variant, orders_by_loc)
            return finder.path_exists(order.supported_source, order.target)
        return False


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

    def __init__(self, unit: Unit) -> None:
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

    def is_legal(
        self,
        variant: Variant,
        units_by_loc: Dict[str, Unit],
        orders_by_loc: Dict[str, "Order"],
    ) -> bool:
        """
        Whether this order's static form is valid against the variant —
        adjacency, unit-type compatibility, supported-unit existence,
        etc. Does not consider resolution-time effects (bounces, support
        cuts, dislodgements).

        Implemented in terms of `validate`; subclasses customise by
        declaring `LEGALITY_CHECKS`, not by overriding this method.
        """
        return self.validate(variant, units_by_loc, orders_by_loc) is None

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
        if army_source == destination:
            return False
        candidates = self._candidates(army_source, destination)
        if excluded is not None:
            candidates = candidates - excluded
        if not candidates:
            return False
        frontier = {
            sea
            for sea in candidates
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
                    if neighbour in candidates and neighbour not in visited:
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
        order = self.context.orders.get(self.province)
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
        order = self.context.orders.get(self.province)
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
        if attacker.unit.location == self.support.cut_exception_location():
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
        defender_nation = self._defender_nation_optimistic()
        if defender_nation == self.move.unit.nation:
            return 0
        supports = self.context.attack_supports_of(self.move)
        active = sum(1 for s in supports if self.context.support_active(s, defender_nation))
        return 1 + active

    def _defender_nation(self) -> Any:
        """Returns the effective defender's nation, None for empty, or _UNDECIDED."""
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            return h2h.unit.nation
        defender_dec = self.context.effective_defender.get(self.move.target)
        if defender_dec is None or not defender_dec.resolved:
            return _UNDECIDED
        defender = defender_dec.value
        return defender.unit.nation if defender is not None else None

    def _defender_nation_optimistic(self) -> Optional[str]:
        """Same as _defender_nation but assumes 'defender stays' when undecided."""
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            return h2h.unit.nation
        defender_dec = self.context.effective_defender.get(self.move.target)
        if defender_dec is not None and defender_dec.resolved:
            defender = defender_dec.value
            return defender.unit.nation if defender is not None else None
        order = self.context.orders.get(self.move.target)
        return order.unit.nation if order is not None else None

    def _possible_defender_nations(self) -> set:
        """Nations that could be the defender at the target after resolution."""
        nations: set = set()
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            nations.add(h2h.unit.nation)
        target_order = self.context.orders.get(self.move.target)
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
        active = sum(1 for s in supports if self.context.support_active(s))
        return 1 + active

    def _default(self) -> Any:
        supports = self.context.attack_supports_of(self.move)
        active = sum(1 for s in supports if self.context.support_active(s))
        return 1 + active


class HoldStrengthDecision(Decision):
    def __init__(self, context: "DecisionContext", province: str) -> None:
        super().__init__(context)
        self.province = province

    def _decide(self) -> Any:
        order = self.context.orders.get(self.province)
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
        active = sum(1 for s in supports if self.context.support_active(s))
        return 1 + active

    def _default(self) -> Any:
        order = self.context.orders.get(self.province)
        if order is None:
            return 1
        if isinstance(order, MoveOrder) and order.status != ResolutionType.ILLEGAL:
            move_dec = self.context.move_resolution.get(order)
            if move_dec is not None and move_dec.value == ResolutionType.OK:
                return 0
        supports = self.context.hold_supports_of(order)
        active = sum(1 for s in supports if self.context.support_active(s))
        return 1 + active


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
        active = sum(1 for s in supports if self.context.support_active(s))
        return 1 + active

    def _default(self) -> Any:
        h2h = self.context.head_to_head_opponent(self.move)
        if h2h is not None:
            h2h_dec = self.context.move_resolution.get(h2h)
            if h2h_dec is not None and h2h_dec.value == ResolutionType.OK:
                return 0
        supports = self.context.attack_supports_of(self.move)
        active = sum(1 for s in supports if self.context.support_active(s))
        return 1 + active


class DislodgementDecision(Decision):
    def __init__(self, context: "DecisionContext", province: str) -> None:
        super().__init__(context)
        self.province = province

    def _decide(self) -> Any:
        defender_dec = self.context.effective_defender.get(self.province)
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
        if attacker.status == ResolutionType.ILLEGAL:
            return True
        move_dec = self.context.move_resolution.get(attacker)
        if move_dec is not None and move_dec.value == ResolutionType.BOUNCE:
            return True
        return False


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
        defender_dec = self.context.effective_defender.get(self.move.target)
        if defender_dec is None or not defender_dec.resolved:
            return _UNDECIDED
        if defender_dec.value is None:
            return ResolutionType.OK
        hold_dec = self.context.hold_strength.get(self.move.target)
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
        self.convoy_path_finder = ConvoyPathFinder(self.variant, self.orders)

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

    def _parse_orders(self) -> Dict[str, Order]:
        orders: Dict[str, Order] = {}
        for raw in self.state.orders:
            unit = self.units.get(raw.source)
            if unit is None or unit.nation != raw.nation:
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
            orders[raw.source] = parsed
        for unit in self.units.values():
            if unit.location not in orders:
                orders[unit.location] = HoldOrder(unit)

        # Phase A: Syntactic convoy validation (independent of other orders).
        for order in orders.values():
            if isinstance(order, ConvoyOrder):
                self._validate(order, orders)

        # Phase B: Mark convoys that aren't on any minimal chain as illegal
        # (DATC 6.G.7, 6.G.19). A convoy fleet is redundant if a chain
        # exists for the same (army_source, destination) without it.
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

        # Phase C: Determine requires_convoy for Move orders.
        finder = ConvoyPathFinder(self.variant, orders)
        for order in orders.values():
            if isinstance(order, MoveOrder):
                order.set_convoy_info(self.variant, finder)

        # Phase D: Validate the remaining orders.
        for order in orders.values():
            if not isinstance(order, ConvoyOrder):
                self._validate(order, orders)

        return orders

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
        for province in self.units:
            self.effective_defender[province] = EffectiveDefenderDecision(
                self, province
            )
            self.hold_strength[province] = HoldStrengthDecision(self, province)
            self.dislodgement[province] = DislodgementDecision(self, province)
        # Effective-defender decisions are also needed for move targets that
        # don't currently hold a unit (attacks into empty provinces).
        for order in self.orders.values():
            if isinstance(order, MoveOrder) and order.status != ResolutionType.ILLEGAL:
                if order.target not in self.effective_defender:
                    self.effective_defender[order.target] = EffectiveDefenderDecision(
                        self, order.target
                    )

    def attackers_into(self, location: str) -> List[MoveOrder]:
        return [
            o
            for o in self.orders.values()
            if isinstance(o, MoveOrder)
            and o.target == location
            and o.status != ResolutionType.ILLEGAL
        ]

    def attack_supports_of(self, move: MoveOrder) -> List[SupportMoveOrder]:
        return [
            o
            for o in self.orders.values()
            if isinstance(o, SupportMoveOrder)
            and o.status != ResolutionType.ILLEGAL
            and o.target == move.target
            and o.supported_source == move.unit.location
        ]

    def hold_supports_of(self, order: Order) -> List[SupportHoldOrder]:
        results: List[SupportHoldOrder] = []
        for o in self.orders.values():
            if not isinstance(o, SupportHoldOrder):
                continue
            if o.status == ResolutionType.ILLEGAL:
                continue
            if o.supported_source != order.unit.location:
                continue
            if not self.support_matches(o):
                continue
            results.append(o)
        return results

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
        dis_dec = self.dislodgement.get(s.unit.location)
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
        dis_dec = self.dislodgement.get(s.unit.location)
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
        """
        if isinstance(s, SupportHoldOrder):
            supported = self.orders.get(s.supported_source)
            if supported is None:
                return False
            if isinstance(supported, MoveOrder) and supported.status != ResolutionType.ILLEGAL:
                return False
            return True
        if isinstance(s, SupportMoveOrder):
            supported = self.orders.get(s.supported_source)
            if supported is None or not isinstance(supported, MoveOrder):
                return False
            if supported.status == ResolutionType.ILLEGAL:
                return False
            return supported.target == s.target
        raise TypeError(f"Unknown SupportOrder subclass: {type(s).__name__}")

    def is_successfully_moving(self, order: Order) -> bool:
        if not isinstance(order, MoveOrder):
            return False
        if order.status == ResolutionType.ILLEGAL:
            return False
        move_dec = self.move_resolution.get(order)
        return move_dec is not None and move_dec.value == ResolutionType.OK

    def head_to_head_opponent(self, move: MoveOrder) -> Optional[MoveOrder]:
        candidate = self.orders.get(move.target)
        if candidate is None:
            return None
        if not isinstance(candidate, MoveOrder):
            return None
        if candidate.status == ResolutionType.ILLEGAL:
            return None
        if candidate.target != move.unit.location:
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
        unresolved = [
            move
            for move, dec in self.context.move_resolution.items()
            if not dec.resolved
        ]
        by_source = {m.unit.location: m for m in unresolved}
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
        chain = [start]
        seen = {start.unit.location}
        current = start
        while True:
            nxt = by_source.get(current.target)
            if nxt is None:
                return None
            if nxt.unit.location == start.unit.location:
                return chain
            if nxt.unit.location in seen:
                return None
            chain.append(nxt)
            seen.add(nxt.unit.location)
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
        resolutions = [
            Resolution(
                province=src, resolution=order.status, reason=order.failure_reason
            )
            for src, order in sorted(ctx.orders.items())
        ]
        resolved = self._resolved_state(new_units, resolutions)
        next_phase = self._next_phase()
        if next_phase is None:
            return [resolved]
        return [resolved, self._next_state(new_units, next_phase)]

    def _resolved_state(
        self, new_units: List[Unit], resolutions: List[Resolution]
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
        )

    def _next_state(self, new_units: List[Unit], next_phase: Phase) -> State:
        next_units = [
            Unit(
                nation=u.nation, type=u.type, location=u.location, dislodged=u.dislodged
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
        dis_dec = ctx.dislodgement.get(unit.location)
        return Unit(
            nation=unit.nation,
            type=unit.type,
            location=unit.location,
            dislodged=(dis_dec is not None and dis_dec.value is True),
        )

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
    start_seas: set = set()
    for adjacency in variant.adjacencies_of(army_source):
        if not adjacency.allows(Unit.FLEET):
            continue
        if adjacency.to in sea_fleets:
            start_seas.add(adjacency.to)
    if not start_seas:
        return set()
    component = set(start_seas)
    frontier = set(start_seas)
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


# === OptionsBuilder ===


class OptionsBuilder:
    _ENUMERATORS_BY_PHASE: Dict[str, Tuple[type, ...]] = {
        Phase.MOVEMENT: (HoldOptions, MoveOptions, SupportOptions, ConvoyOptions),
    }

    def __init__(self, variant: Variant) -> None:
        self.variant = variant

    def build(self, state: State) -> List[OrderOption]:
        enumerators = self._ENUMERATORS_BY_PHASE.get(state.phase.type, ())
        units_by_loc: Dict[str, Unit] = {
            u.location: u for u in state.units if not u.dislodged
        }
        return [
            option
            for unit in state.units
            if not unit.dislodged
            for enumerator in enumerators
            for option in enumerator.for_unit(unit, self.variant, units_by_loc)
        ]
