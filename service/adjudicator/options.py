"""Order options generation.

For each phase, enumerates the complete set of legal orders a player could
submit, returned as a flat list of `OrderOption` records. The design lives
outside the `engine.py` rubric — see `docs/options-design.md`.

The core pattern reuses the existing `LEGALITY_CHECKS` from `types.py` as
the authoritative filter so options can't drift from what the engine
accepts. For convoy-dependent enumeration the module falls back to
`convoy_path_exists` over the physical fleet positions on the board,
mirroring godip's options semantics (which don't depend on submitted
convoys). This is documented as the only intentional divergence from the
engine's legality semantics.

Named-coast convention matches godip: the coast id is placed directly in
the location field (`target` for moves, `source` for builds). The
`OrderOption.named_coast` field is unused.

SupportHold representation matches godip's serialization (and the example
the project was given): `target = aux = supported_loc`. The frontend (and
test scaffolding) translates `target = None` when converting to a wire
order for submission.
"""
from __future__ import annotations

from typing import List, Tuple

from .convoy import convoy_path_exists, convoy_path_through_fleet
from .domain import OrderOption, Phase, ProvinceType, State, Unit
from .types import (
    AdjudicationState,
    AdjustmentDisbandOrder,
    BuildOrder,
    ConvoyFleetReachesEndpointsCheck,
    ConvoyOrder,
    MoveOrder,
    MoveTargetIsReachableCheck,
    OrderType,
    RetreatOrder,
    StateView,
    SupportHoldOrder,
    SupportMoveOrder,
    SupportMoveSupportedCanReachCheck,
)


def get_options(state: State) -> List[OrderOption]:
    """Public entry point. Returns all legal orders for the phase's
    eligible units across every nation. Callers filter by nation if
    needed. Raises NotImplementedError for phase types other than
    Movement, Retreat, or Adjustment."""
    adj = AdjudicationState(
        variant=state.variant,
        phase=state.phase,
        units=tuple(state.units),
        supply_centers=tuple(state.supply_centers),
        raw_orders=(),
        contested_provinces=tuple(state.contested_provinces),
    )
    view = StateView(adj)
    phase_type = state.phase.type
    if phase_type == Phase.MOVEMENT:
        return _movement_options(view)
    if phase_type == Phase.RETREAT:
        return _retreat_options(view)
    if phase_type == Phase.ADJUSTMENT:
        return _adjustment_options(view)
    raise NotImplementedError(f"Phase type {phase_type!r} is not supported.")


# === Movement phase ===


def _movement_options(view: StateView) -> List[OrderOption]:
    options: List[OrderOption] = []
    variant = view.variant()
    units_view = view.units()
    standing_items = tuple(sorted(units_view.standing_by_loc().items()))
    sea_fleet_locs = tuple(
        u.location
        for u in units_view.all()
        if not u.dislodged
        and u.type == Unit.FLEET
        and view.province(variant.parent_of(u.location)).is_sea()
    )
    all_locations = tuple(
        list(variant.provinces.keys()) + list(variant.named_coasts.keys())
    )
    for source_loc, unit in standing_items:
        options.append(
            OrderOption(
                source=source_loc,
                order_type=OrderType.HOLD,
                target=None,
                aux=None,
                unit_type=None,
                named_coast=None,
            )
        )
        for target in all_locations:
            order = MoveOrder(
                nation=unit.nation,
                source=source_loc,
                target=target,
                unit_type=unit.type,
            )
            if _move_is_orderable(view, order, sea_fleet_locs):
                options.append(
                    OrderOption(
                        source=source_loc,
                        order_type=OrderType.MOVE,
                        target=target,
                        aux=None,
                        unit_type=None,
                        named_coast=None,
                    )
                )
            # godip emits a parallel "MoveViaConvoy" option whenever the
            # army could reach the target via a chain of fleets currently
            # on the board. This is the wire-format channel for the
            # explicit via-convoy intent (DATC 6.G.1/5 head-to-head
            # exception).
            if unit.type == Unit.ARMY and _move_has_convoy_path(
                view, order, sea_fleet_locs
            ):
                options.append(
                    OrderOption(
                        source=source_loc,
                        order_type="MoveViaConvoy",
                        target=target,
                        aux=None,
                        unit_type=None,
                        named_coast=None,
                    )
                )
        options.extend(
            _support_options(
                view, unit, source_loc, sea_fleet_locs, standing_items
            )
        )
        if unit.type == Unit.FLEET and view.province(
            variant.parent_of(source_loc)
        ).is_sea():
            options.extend(
                _convoy_options(
                    view, unit, source_loc, sea_fleet_locs, standing_items
                )
            )
    return options


def _move_is_orderable(
    view: StateView, order: MoveOrder, sea_fleet_locs: Tuple[str, ...]
) -> bool:
    if _fleet_target_is_bare_multi_coast(view, order):
        return False
    for check_cls in MoveOrder.LEGALITY_CHECKS:
        if check_cls.check(view, order):
            continue
        if check_cls is MoveTargetIsReachableCheck and _move_has_convoy_path(
            view, order, sea_fleet_locs
        ):
            continue
        return False
    return True


def _move_has_convoy_path(
    view: StateView, order: MoveOrder, sea_fleet_locs: Tuple[str, ...]
) -> bool:
    if order.unit_type != Unit.ARMY:
        return False
    variant = view.variant()
    target_parent = variant.parent_of(order.target)
    # Convoyed army moves are always to a bare parent — armies ignore coasts.
    if order.target != target_parent:
        return False
    source_parent = variant.parent_of(order.source)
    # Source must be coastal OR convoyable_capable
    source_prov = variant.provinces.get(source_parent)
    if not (view.province(source_parent).is_coastal() or
            (source_prov is not None and source_prov.convoyable_capable)):
        return False
    # Target must be coastal OR convoyable_capable
    target_prov = variant.provinces.get(target_parent)
    if not (view.province(target_parent).is_coastal() or
            (target_prov is not None and target_prov.convoyable_capable)):
        return False
    if not sea_fleet_locs:
        return False
    return convoy_path_exists(view, source_parent, target_parent, sea_fleet_locs)


def _fleet_target_is_bare_multi_coast(view: StateView, order: MoveOrder) -> bool:
    """A fleet enters a multi-coast province only via a specific named
    coast, never the bare parent — godip models this in its fleet
    adjacency graph. Armies are unaffected: they move to the bare parent
    and ignore coasts."""
    if order.unit_type != Unit.FLEET:
        return False
    variant = view.variant()
    if order.target != variant.parent_of(order.target):
        return False
    return bool(variant.coasts_of(order.target))


def _reachable_provinces(variant, source_loc: str, unit_type: str) -> set:
    result = set()
    for adj in variant.adjacencies_of(source_loc):
        if adj.allows(unit_type):
            result.add(variant.parent_of(adj.to))
    return result


def _support_options(
    view: StateView,
    supporter: Unit,
    source_loc: str,
    sea_fleet_locs: Tuple[str, ...],
    standing_items: Tuple[Tuple[str, Unit], ...],
) -> List[OrderOption]:
    options: List[OrderOption] = []
    variant = view.variant()
    source_parent = variant.parent_of(source_loc)
    for supported_loc, _ in standing_items:
        if variant.parent_of(supported_loc) == source_parent:
            continue
        order = SupportHoldOrder(
            nation=supporter.nation,
            source=source_loc,
            supported_source=supported_loc,
            unit_type=supporter.type,
        )
        if all(c.check(view, order) for c in SupportHoldOrder.LEGALITY_CHECKS):
            supported_parent = variant.parent_of(supported_loc)
            options.append(
                OrderOption(
                    source=source_loc,
                    order_type=OrderType.SUPPORT,
                    target=supported_parent,
                    aux=supported_parent,
                    unit_type=None,
                    named_coast=None,
                )
            )
    supporter_targets = _reachable_provinces(variant, source_loc, supporter.type)
    supporter_targets.discard(source_parent)
    for mover_loc, mover in standing_items:
        if variant.parent_of(mover_loc) == source_parent:
            continue
        for target in supporter_targets:
            order = SupportMoveOrder(
                nation=supporter.nation,
                source=source_loc,
                supported_source=mover_loc,
                target=target,
                unit_type=supporter.type,
            )
            if _support_move_is_orderable(view, order, mover, sea_fleet_locs):
                mover_parent = variant.parent_of(mover_loc)
                options.append(
                    OrderOption(
                        source=source_loc,
                        order_type=OrderType.SUPPORT,
                        target=target,
                        aux=mover_parent,
                        unit_type=None,
                        named_coast=None,
                    )
                )
    return options


def _support_move_is_orderable(
    view: StateView,
    order: SupportMoveOrder,
    mover: Unit,
    sea_fleet_locs: Tuple[str, ...],
) -> bool:
    for check_cls in SupportMoveOrder.LEGALITY_CHECKS:
        if check_cls.check(view, order):
            continue
        if (
            check_cls is SupportMoveSupportedCanReachCheck
            and _supported_can_convoy(view, order, mover, sea_fleet_locs)
        ):
            continue
        return False
    return True


def _supported_can_convoy(
    view: StateView,
    order: SupportMoveOrder,
    mover: Unit,
    sea_fleet_locs: Tuple[str, ...],
) -> bool:
    if mover.type != Unit.ARMY:
        return False
    variant = view.variant()
    target_parent = variant.parent_of(order.target)
    if order.target != target_parent:
        return False
    source_parent = variant.parent_of(mover.location)
    source_prov = variant.provinces.get(source_parent)
    if not (view.province(source_parent).is_coastal() or
            (source_prov is not None and source_prov.convoyable_capable)):
        return False
    target_prov = variant.provinces.get(target_parent)
    if not (view.province(target_parent).is_coastal() or
            (target_prov is not None and target_prov.convoyable_capable)):
        return False
    # Exclude the supporter itself from the convoy chain (godip's
    # `noConvoy` argument): if the supporter is also the only fleet,
    # no third party can carry the army.
    usable_fleets = tuple(loc for loc in sea_fleet_locs if loc != order.source)
    if not usable_fleets:
        return False
    return convoy_path_exists(view, source_parent, target_parent, usable_fleets)


def _convoy_options(
    view: StateView,
    fleet: Unit,
    source_loc: str,
    sea_fleet_locs: Tuple[str, ...],
    standing_items: Tuple[Tuple[str, Unit], ...],
) -> List[OrderOption]:
    options: List[OrderOption] = []
    variant = view.variant()
    army_source_parents = sorted(
        {variant.parent_of(loc) for loc, u in standing_items if u.type == Unit.ARMY}
    )
    coastal_parents = sorted(
        pid
        for pid, p in variant.provinces.items()
        if p.type != ProvinceType.SEA and (variant.has_fleet_access(pid) or p.convoyable_capable)
    )
    for army_source in army_source_parents:
        for army_target in coastal_parents:
            if army_source == army_target:
                continue
            order = ConvoyOrder(
                nation=fleet.nation,
                source=source_loc,
                army_source=army_source,
                army_target=army_target,
                unit_type=fleet.type,
            )
            if _convoy_is_orderable(view, order, sea_fleet_locs):
                options.append(
                    OrderOption(
                        source=source_loc,
                        order_type=OrderType.CONVOY,
                        target=army_target,
                        aux=army_source,
                        unit_type=None,
                        named_coast=None,
                    )
                )
    return options


def _convoy_is_orderable(
    view: StateView, order: ConvoyOrder, sea_fleet_locs: Tuple[str, ...]
) -> bool:
    # ConvoyFleetReachesEndpointsCheck is the engine's order-legality
    # check: a purely topological reachability test that is intentionally
    # lenient. Options instead require a convoy chain through the fleets
    # actually on the board, with this fleet on it — strictly stronger,
    # so it fully replaces the topological check rather than supplementing
    # it. See the module docstring and docs/options-design.md.
    for check_cls in ConvoyOrder.LEGALITY_CHECKS:
        if check_cls is ConvoyFleetReachesEndpointsCheck:
            continue
        if not check_cls.check(view, order):
            return False
    return _convoy_has_real_path(view, order, sea_fleet_locs)


def _convoy_has_real_path(
    view: StateView, order: ConvoyOrder, sea_fleet_locs: Tuple[str, ...]
) -> bool:
    if not sea_fleet_locs:
        return False
    variant = view.variant()
    return convoy_path_through_fleet(
        view,
        variant.parent_of(order.army_source),
        variant.parent_of(order.army_target),
        order.source,
        sea_fleet_locs,
    )


# === Retreat phase ===


def _retreat_options(view: StateView) -> List[OrderOption]:
    options: List[OrderOption] = []
    variant = view.variant()
    units_view = view.units()
    dislodged = sorted(units_view.dislodged_by_loc().items())
    all_locations = tuple(
        list(variant.provinces.keys()) + list(variant.named_coasts.keys())
    )
    for source_loc, unit in dislodged:
        options.append(
            OrderOption(
                source=source_loc,
                order_type=OrderType.DISBAND,
                target=None,
                aux=None,
                unit_type=None,
                named_coast=None,
            )
        )
        for target in all_locations:
            order = RetreatOrder(
                nation=unit.nation,
                source=source_loc,
                target=target,
                unit_type=unit.type,
                dislodged_from=unit.dislodged_from,
            )
            if all(c.check(view, order) for c in RetreatOrder.LEGALITY_CHECKS):
                options.append(
                    OrderOption(
                        source=source_loc,
                        order_type=OrderType.RETREAT,
                        target=target,
                        aux=None,
                        unit_type=None,
                        named_coast=None,
                    )
                )
    return options


# === Adjustment phase ===


def _adjustment_options(view: StateView) -> List[OrderOption]:
    options: List[OrderOption] = []
    variant = view.variant()
    units_view = view.units()
    standing = sorted(units_view.standing_by_loc().items())
    nations = [n.id for n in variant.nations]
    for nation_id in nations:
        nation_view = view.nation(nation_id)
        if nation_view.allowed_builds() <= 0:
            continue
        for sc_parent in sorted(nation_view.owned_supply_centers()):
            province = variant.provinces.get(sc_parent)
            if province is None or not province.supply_center:
                continue
            if view.province(sc_parent).is_occupied():
                continue
            army_order = BuildOrder(
                nation=nation_id,
                location=sc_parent,
                unit_type=Unit.ARMY,
            )
            if all(c.check(view, army_order) for c in BuildOrder.LEGALITY_CHECKS):
                options.append(
                    OrderOption(
                        source=sc_parent,
                        order_type=OrderType.BUILD,
                        target=sc_parent,
                        aux=None,
                        unit_type=Unit.ARMY,
                        named_coast=None,
                    )
                )
            coasts = variant.coasts_of(sc_parent)
            fleet_locations = list(coasts) if coasts else [sc_parent]
            for fleet_loc in fleet_locations:
                fleet_order = BuildOrder(
                    nation=nation_id,
                    location=fleet_loc,
                    unit_type=Unit.FLEET,
                )
                if all(c.check(view, fleet_order) for c in BuildOrder.LEGALITY_CHECKS):
                    options.append(
                        OrderOption(
                            source=fleet_loc,
                            order_type=OrderType.BUILD,
                            target=fleet_loc,
                            aux=None,
                            unit_type=Unit.FLEET,
                            named_coast=None,
                        )
                    )
    for nation_id in nations:
        nation_view = view.nation(nation_id)
        if nation_view.required_disbands() <= 0:
            continue
        for loc, unit in standing:
            if unit.nation != nation_id:
                continue
            order = AdjustmentDisbandOrder(
                nation=nation_id,
                location=loc,
                unit_type=unit.type,
            )
            if all(c.check(view, order) for c in AdjustmentDisbandOrder.LEGALITY_CHECKS):
                options.append(
                    OrderOption(
                        source=loc,
                        order_type=OrderType.DISBAND,
                        target=None,
                        aux=None,
                        unit_type=None,
                        named_coast=None,
                    )
                )
    return options
