"""Convert the Python adjudicator's flat option list into godip's nested
wire-format options dict.

The Python engine emits options as a flat list of ``OrderOption`` records.
Existing consumers (``transform_options`` in ``phase/utils.py`` and the
frontend's option-tree walker) expect godip's nested
``{nation: {province: {Next: {OrderType: {Next: {SrcProvince: {Next: ...}}}}}}}``
shape. This adapter rebuilds that shape so we can swap the godip HTTP call
for the in-process engine without touching downstream consumers.

Quirks worth knowing:
  - In Retreat phases godip emits retreat options under the ``Move`` order
    type. The Python engine uses ``Retreat`` natively; the adapter rewrites
    it back to ``Move`` so the wire format matches.
  - Build options for a multi-coast supply center are emitted under
    *each* named coast: at ``stp/nc`` the inner tree has both
    ``Army → stp`` (Army builds key off the parent province) and
    ``Fleet → stp/nc`` (Fleet builds key off this coast). The
    ``_merge_named_coast_build_options`` step in ``transform_options``
    is what folds those back into a single parent-level entry.
  - For everything except multi-coast Builds the top-level province key
    is the parent province — even when the unit sits on a named coast.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from adjudicator.domain import OrderOption, SupplyCenter, Unit, Variant


_PROVINCE = "Province"
_ORDER_TYPE = "OrderType"
_SRC_PROVINCE = "SrcProvince"
_UNIT_TYPE = "UnitType"


def python_options_to_godip_dict(
    options: Iterable[OrderOption],
    units: Iterable[Unit],
    supply_centers: Iterable[SupplyCenter],
    variant: Variant,
    phase_type: str,
) -> Dict[str, Any]:
    is_retreat = phase_type == "Retreat"

    nation_name_by_id = {nation.id: nation.name for nation in variant.nations}

    standing_nation_by_loc: Dict[str, str] = {}
    dislodged_nation_by_loc: Dict[str, str] = {}
    for unit in units:
        if unit.dislodged:
            dislodged_nation_by_loc[unit.location] = unit.nation
        else:
            standing_nation_by_loc[unit.location] = unit.nation

    sc_nation_by_province = {sc.province: sc.nation for sc in supply_centers}

    result: Dict[str, Any] = {nation.name: {} for nation in variant.nations}

    build_options: List[OrderOption] = []
    for option in options:
        if option.order_type == "Build":
            build_options.append(option)
            continue
        _add_movement_option(
            result,
            option,
            variant,
            is_retreat,
            standing_nation_by_loc,
            dislodged_nation_by_loc,
            sc_nation_by_province,
            nation_name_by_id,
        )

    _add_build_options(
        result,
        build_options,
        variant,
        sc_nation_by_province,
        nation_name_by_id,
    )

    return result


def _add_movement_option(
    result: Dict[str, Any],
    option: OrderOption,
    variant: Variant,
    is_retreat: bool,
    standing_by_loc: Dict[str, str],
    dislodged_by_loc: Dict[str, str],
    sc_by_province: Dict[str, str],
    nation_name_by_id: Dict[str, str],
) -> None:
    if is_retreat:
        nation_id = dislodged_by_loc.get(option.source)
    else:
        nation_id = standing_by_loc.get(option.source)
        if nation_id is None:
            nation_id = sc_by_province.get(variant.parent_of(option.source))
    if nation_id is None:
        return
    nation_name = nation_name_by_id.get(nation_id, nation_id)

    godip_source = variant.parent_of(option.source)
    godip_order_type = "Move" if is_retreat and option.order_type == "Retreat" else option.order_type

    nation_tree = result.setdefault(nation_name, {})
    province_tree = nation_tree.setdefault(
        godip_source, {"Next": {}, "Type": _PROVINCE}
    )
    order_type_tree = province_tree["Next"].setdefault(
        godip_order_type, {"Next": {}, "Type": _ORDER_TYPE}
    )
    src_tree = order_type_tree["Next"].setdefault(
        godip_source, {"Next": {}, "Type": _SRC_PROVINCE}
    )

    if option.order_type in ("Hold", "Disband"):
        return

    if option.order_type in ("Move", "MoveViaConvoy", "Retreat"):
        src_tree["Next"].setdefault(option.target, {"Next": {}, "Type": _PROVINCE})
        return

    if option.order_type in ("Support", "Convoy"):
        aux_tree = src_tree["Next"].setdefault(
            option.aux, {"Next": {}, "Type": _PROVINCE}
        )
        aux_tree["Next"].setdefault(option.target, {"Next": {}, "Type": _PROVINCE})


def _add_build_options(
    result: Dict[str, Any],
    build_options: Iterable[OrderOption],
    variant: Variant,
    sc_by_province: Dict[str, str],
    nation_name_by_id: Dict[str, str],
) -> None:
    """Emit Build options in godip's per-coast layout.

    Groups Python's flat list of ``(source, unit_type)`` Builds by parent
    province, then for each parent decides between two layouts:
      - If the parent has named coasts AND a Fleet build is enumerated at
        any of those coasts: emit a top-level entry at *each* named coast,
        containing ``Build.Next.Army.Next.parent`` plus that coast's
        ``Build.Next.Fleet.Next.coast``. godip is redundant here; the
        downstream ``_merge_named_coast_build_options`` step relies on
        the redundancy to fold the per-coast entries back into a single
        parent-level merged entry.
      - Otherwise: emit a single top-level entry at the parent province
        with whatever unit types are buildable (inland → Army only,
        single-coast → Army + Fleet, etc.).
    """
    # parent → unit_type → {src locations}
    grouped: Dict[Tuple[str, str], Dict[str, set]] = defaultdict(lambda: defaultdict(set))
    for option in build_options:
        parent = variant.parent_of(option.source)
        nation_id = sc_by_province.get(parent)
        if nation_id is None:
            continue
        unit_type = option.unit_type or "Army"
        grouped[(nation_id, parent)][unit_type].add(option.source)

    for (nation_id, parent), unit_type_sources in grouped.items():
        nation_name = nation_name_by_id.get(nation_id, nation_id)
        nation_tree = result.setdefault(nation_name, {})

        coasts = variant.coasts_of(parent)
        fleet_coasts = {
            src for src in unit_type_sources.get("Fleet", set()) if src in coasts
        }

        if coasts and fleet_coasts:
            # godip redundancy: emit an entry per named coast.
            for coast in fleet_coasts:
                province_tree = nation_tree.setdefault(
                    coast, {"Next": {}, "Type": _PROVINCE}
                )
                order_type_tree = province_tree["Next"].setdefault(
                    "Build", {"Next": {}, "Type": _ORDER_TYPE}
                )
                if "Army" in unit_type_sources:
                    order_type_tree["Next"].setdefault(
                        "Army",
                        {
                            "Next": {parent: {"Next": {}, "Type": _SRC_PROVINCE}},
                            "Type": _UNIT_TYPE,
                        },
                    )
                order_type_tree["Next"].setdefault(
                    "Fleet",
                    {
                        "Next": {coast: {"Next": {}, "Type": _SRC_PROVINCE}},
                        "Type": _UNIT_TYPE,
                    },
                )
            continue

        # No named coasts, or no Fleet at a coast — emit a single parent
        # entry with whatever unit types are buildable here.
        province_tree = nation_tree.setdefault(
            parent, {"Next": {}, "Type": _PROVINCE}
        )
        order_type_tree = province_tree["Next"].setdefault(
            "Build", {"Next": {}, "Type": _ORDER_TYPE}
        )
        for unit_type in sorted(unit_type_sources):
            order_type_tree["Next"].setdefault(
                unit_type,
                {
                    "Next": {parent: {"Next": {}, "Type": _SRC_PROVINCE}},
                    "Type": _UNIT_TYPE,
                },
            )
