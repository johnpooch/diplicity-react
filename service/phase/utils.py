from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from common.constants import OrderType, PhaseFrequency, PhaseType, ProvinceType


def format_time_remaining(seconds):
    if seconds >= 2 * 3600:
        return f"{int(seconds // 3600)} hours"
    if seconds >= 3600:
        return "1 hour"
    if seconds >= 2 * 60:
        return f"{int(seconds // 60)} minutes"
    return "less than a minute"


def format_deadline(dt, tz_name=None):
    if tz_name:
        try:
            dt_local = dt.astimezone(ZoneInfo(tz_name))
            return dt_local.strftime("%b %d, %Y at %I:%M %p") + f" {tz_name}"
        except ZoneInfoNotFoundError:
            pass
    return dt.strftime("%b %d, %Y at %I:%M %p UTC")


def build_notification_body(
    orders_confirmed, is_fixed_time, orders_given, total_units, time_left, extensions_remaining,
    is_adjustment=False,
):
    if extensions_remaining > 0:
        nmr_suffix = "If no orders given, the deadline will extend, but you'll lose an extension."
    elif is_adjustment:
        nmr_suffix = "If no orders given, adjustments will be made automatically."
    else:
        nmr_suffix = "If no orders given, the game will stop waiting for you for next turns."

    if is_fixed_time:
        if orders_given == total_units:
            if orders_confirmed:
                return None
            return (
                f"All orders ready. Confirm to advance the game early — "
                f"the next deadline may move sooner too. {time_left} remaining."
            )
        if orders_given > 0:
            return (
                f"Deadline approaching - orders incomplete. "
                f"{orders_given}/{total_units} units have an order. "
                f"{time_left} to adjust your orders."
            )
        return (
            f"Deadline approaching - no orders given. "
            f"Your units have not received orders. "
            f"{time_left} to adjust your orders. "
            f"{nmr_suffix}"
        )
    else:
        if orders_confirmed:
            return None
        if orders_given == total_units:
            return (
                f"Deadline approaching - orders ready, waiting confirmation. "
                f"You have {time_left} to adjust your orders. "
                f"If not confirmed, standing orders will execute."
            )
        if orders_given > 0:
            return (
                f"Deadline approaching - orders incomplete. "
                f"{orders_given}/{total_units} units have an order. "
                f"{time_left} to adjust your orders. "
                f"If not confirmed, standing orders will execute."
            )
        return (
            f"Deadline approaching - no orders given. "
            f"Your units don't have orders yet. "
            f"{time_left} to provide orders. "
            f"{nmr_suffix}"
        )


def transform_options(raw_options):
    """
    Transform godip options into simplified structure.

    1. Remove "Next" nesting - flatten to direct key access
    2. Remove "Type" metadata
    3. Remove SrcProvince confirmation layer
    4. Merge named coast build options under parent province
    """
    transformed = {}

    for nation, nation_options in raw_options.items():
        # First, merge any named coast provinces for build orders
        merged_provinces = _merge_named_coast_build_options(nation_options)

        transformed[nation] = {}

        for province_id, province_data in merged_provinces.items():
            transformed[nation][province_id] = _transform_province_options(province_data)

    return transformed


def _merge_named_coast_build_options(nation_options):
    """
    Merge named coast provinces for build orders under their parent province.

    For example, merge stp/nc and stp/sc build options into a single stp entry
    where Army uses parent and Fleet offers coast selection.
    """
    # Find all named coast provinces
    named_coast_ids = [p for p in nation_options.keys() if "/" in p]

    if not named_coast_ids:
        return nation_options

    # Group named coasts by parent
    parent_groups = {}
    for coast_id in named_coast_ids:
        parent_id = coast_id.split("/")[0]
        if parent_id not in parent_groups:
            parent_groups[parent_id] = []
        parent_groups[parent_id].append(coast_id)

    # Build the merged result
    result = {}
    processed_coasts = set()

    for province_id, province_data in nation_options.items():
        # Skip if this coast was already processed
        if province_id in processed_coasts:
            continue

        # Check if this is a named coast with siblings
        if province_id in named_coast_ids:
            parent_id = province_id.split("/")[0]
            coast_list = parent_groups[parent_id]

            # Only merge if there are multiple coasts AND they have Build orders
            if len(coast_list) > 1 and _has_build_order(province_data):
                # Merge all coasts into parent
                merged_data = _merge_build_options_for_coasts(
                    {coast_id: nation_options[coast_id] for coast_id in coast_list}
                )
                result[parent_id] = merged_data
                processed_coasts.update(coast_list)
            else:
                # Single coast or no build - keep as is
                result[province_id] = province_data
        else:
            # Regular province
            result[province_id] = province_data

    return result


def _has_build_order(province_data):
    """Check if a province has a Build order."""
    if not isinstance(province_data, dict):
        return False
    next_data = province_data.get("Next", {})
    return "Build" in next_data


def _merge_build_options_for_coasts(coast_provinces):
    """
    Merge build options from multiple named coasts.

    Army: Uses parent province (same for all coasts)
    Fleet: Collects all coast options for selection
    """
    # Take structure from first coast
    first_coast_id = list(coast_provinces.keys())[0]
    first_coast_data = coast_provinces[first_coast_id]

    # Clone the structure
    merged = {"Next": {"Build": {"Next": {}, "Type": "OrderType"}}, "Type": "Province"}

    # Copy Filter if it exists
    if "Filter" in first_coast_data:
        merged["Filter"] = first_coast_data["Filter"]

    # Collect Fleet options from all coasts
    fleet_src_provinces = {}
    army_src_province = None

    for coast_id, coast_data in coast_provinces.items():
        build_data = coast_data.get("Next", {}).get("Build", {}).get("Next", {})

        # Get Army SrcProvince (should be the same parent for all)
        if "Army" in build_data:
            army_data = build_data["Army"].get("Next", {})
            if army_src_province is None and army_data:
                army_src_province = list(army_data.keys())[0]

        # Get Fleet SrcProvince (specific to this coast)
        if "Fleet" in build_data:
            fleet_data = build_data["Fleet"].get("Next", {})
            if fleet_data:
                fleet_src = list(fleet_data.keys())[0]
                fleet_src_provinces[fleet_src] = {}

    # Build Army option (uses parent)
    if army_src_province:
        merged["Next"]["Build"]["Next"]["Army"] = {
            "Next": {army_src_province: {"Next": {}, "Type": "SrcProvince"}},
            "Type": "UnitType",
        }

    # Build Fleet option (offers coast selection)
    if fleet_src_provinces:
        merged["Next"]["Build"]["Next"]["Fleet"] = {"Next": fleet_src_provinces, "Type": "UnitType"}

    return merged


def _transform_province_options(province_data):
    """
    Transform a single province's options tree.
    """
    if not isinstance(province_data, dict):
        return {}

    # Navigate into the "Next" layer if it exists
    order_types = province_data.get("Next", {})

    result = {}

    for order_type, order_data in order_types.items():
        result[order_type] = _transform_order_type_options(order_data)

    return result


def _transform_order_type_options(order_data):
    """
    Transform options after an order type is selected.
    Remove the SrcProvince confirmation layer.
    Handle UnitType layer for Build orders.
    """
    if not isinstance(order_data, dict):
        return {}

    # Get the next level
    next_level = order_data.get("Next", {})

    # Check if this is a SrcProvince confirmation layer (single key, Type=SrcProvince)
    if len(next_level) == 1:
        single_key = list(next_level.keys())[0]
        single_value = next_level[single_key]

        if isinstance(single_value, dict) and single_value.get("Type") == "SrcProvince":
            # This is a SrcProvince confirmation - skip it and get what's after
            provinces_after = single_value.get("Next", {})
            # Clean up the province entries by removing Type and Next metadata
            return _clean_province_dict(provinces_after)

    # Check if this is a UnitType layer (for Build orders)
    # Each unit type (Army, Fleet) has a SrcProvince confirmation beneath it
    result = {}
    for key, value in next_level.items():
        if isinstance(value, dict) and value.get("Type") == "UnitType":
            # This is a unit type - recursively transform what's underneath
            result[key] = _transform_unit_type_options(value)
        elif isinstance(value, dict) and value.get("Type") == "Province":
            # This is a province option (for Support/Convoy)
            inner_next = value.get("Next", {})
            if not inner_next:
                result[key] = {}
            else:
                result[key] = _clean_province_dict(inner_next)
        else:
            # Unknown structure - just clean it
            result[key] = {}

    return result


def _transform_unit_type_options(unit_type_data):
    """
    Transform options after a unit type is selected (for Build orders).
    Remove the SrcProvince confirmation layer OR return coast options.
    """
    if not isinstance(unit_type_data, dict):
        return {}

    next_level = unit_type_data.get("Next", {})

    # Check for SrcProvince confirmation (single province)
    if len(next_level) == 1:
        single_key = list(next_level.keys())[0]
        single_value = next_level[single_key]

        if isinstance(single_value, dict) and single_value.get("Type") == "SrcProvince":
            # SrcProvince confirmation - this is terminal for builds
            return {}

    # If there are multiple options, they're coast selections (for Fleet builds on named coasts)
    # Just return them as empty dicts (they're terminal)
    if next_level:
        return {key: {} for key in next_level.keys()}

    return {}


def _clean_province_dict(provinces):
    """
    Remove Type and Next metadata from province entries.
    Convert {province: {Next: {}, Type: Province}} to {province: {}}
    Group named coast provinces under their parent.
    """
    # First, identify named coast provinces
    named_coasts = _group_named_coasts(provinces)

    cleaned = {}
    processed_coasts = set()

    for province_id, province_data in provinces.items():
        # Skip if this named coast was already processed as part of a group
        if province_id in processed_coasts:
            continue

        # Check if this province has named coast siblings
        if province_id in named_coasts:
            parent_id = named_coasts[province_id]["parent"]
            coast_ids = named_coasts[province_id]["coasts"]

            # Group all named coasts under parent province
            cleaned[parent_id] = {}
            for coast_id in coast_ids:
                cleaned[parent_id][coast_id] = {}
                processed_coasts.add(coast_id)
        else:
            # Regular province
            if isinstance(province_data, dict):
                # For terminal provinces (no further choices), just return empty dict
                next_options = province_data.get("Next", {})
                if not next_options:
                    cleaned[province_id] = {}
                else:
                    # If there are further options, recursively clean them
                    cleaned[province_id] = _clean_province_dict(next_options)
            else:
                cleaned[province_id] = {}

    return cleaned


def _group_named_coasts(provinces):
    """
    Identify named coast provinces and group them by parent.
    Returns a dict mapping each named coast to its parent and sibling coasts.

    Example: {"spa/nc": {"parent": "spa", "coasts": ["spa/nc", "spa/sc"]}, ...}
    """
    # Find all named coast provinces (contain '/')
    named_coast_ids = [p for p in provinces.keys() if "/" in p]

    if not named_coast_ids:
        return {}

    # Group by parent province
    parent_groups = {}
    for coast_id in named_coast_ids:
        parent_id = coast_id.split("/")[0]
        if parent_id not in parent_groups:
            parent_groups[parent_id] = []
        parent_groups[parent_id].append(coast_id)

    # Group ALL named coasts under parent for consistency
    result = {}
    for parent_id, coast_list in parent_groups.items():
        for coast_id in coast_list:
            result[coast_id] = {"parent": parent_id, "coasts": sorted(coast_list)}

    return result


FREQUENCY_INTERVALS = {
    PhaseFrequency.HOURLY: timedelta(hours=1),
    PhaseFrequency.DAILY: timedelta(days=1),
    PhaseFrequency.EVERY_2_DAYS: timedelta(days=2),
    PhaseFrequency.WEEKLY: timedelta(weeks=1),
}


def compress_deadline(next_deadline, frequency, now):
    interval = FREQUENCY_INTERVALS.get(frequency)
    if not interval:
        return next_deadline
    candidate = next_deadline
    while (candidate - interval) - now >= interval:
        candidate -= interval
    return candidate


def calculate_next_fixed_deadline(
    target_time,
    frequency,
    tz_name,
    reference_time=None,
    is_first_phase=False,
):
    if reference_time is None:
        reference_time = timezone.now()

    tz = ZoneInfo(tz_name)
    local_now = reference_time.astimezone(tz)

    if frequency == PhaseFrequency.HOURLY:
        if is_first_phase:
            candidate = local_now.replace(
                hour=target_time.hour,
                minute=target_time.minute,
                second=0,
                microsecond=0,
            )
            if candidate <= local_now:
                candidate += timedelta(days=1)
            next_deadline = candidate + FREQUENCY_INTERVALS[frequency]
        else:
            candidate = local_now.replace(
                minute=target_time.minute,
                second=0,
                microsecond=0,
            )
            if candidate <= local_now:
                candidate += FREQUENCY_INTERVALS[frequency]
            next_deadline = candidate
    elif frequency == PhaseFrequency.DAILY:
        candidate = local_now.replace(
            hour=target_time.hour,
            minute=target_time.minute,
            second=0,
            microsecond=0,
        )
        if candidate <= local_now:
            candidate += timedelta(days=1)
        next_deadline = candidate
        if is_first_phase:
            next_deadline += FREQUENCY_INTERVALS[frequency]
    elif frequency == PhaseFrequency.EVERY_2_DAYS:
        candidate = local_now.replace(
            hour=target_time.hour,
            minute=target_time.minute,
            second=0,
            microsecond=0,
        )
        if candidate <= local_now:
            candidate += timedelta(days=1)
        min_deadline = local_now + timedelta(days=1)
        while candidate < min_deadline:
            candidate += timedelta(days=1)
        days_from_now = (candidate.date() - local_now.date()).days
        if days_from_now % 2 == 1:
            candidate += timedelta(days=1)
        next_deadline = candidate
        if is_first_phase:
            next_deadline += FREQUENCY_INTERVALS[frequency]
    elif frequency == PhaseFrequency.WEEKLY:
        candidate = local_now.replace(
            hour=target_time.hour,
            minute=target_time.minute,
            second=0,
            microsecond=0,
        )
        if candidate <= local_now:
            candidate += timedelta(days=1)
        min_deadline = local_now + timedelta(days=7)
        while candidate < min_deadline:
            candidate += timedelta(days=1)
        next_deadline = candidate
        if is_first_phase:
            next_deadline += FREQUENCY_INTERVALS[frequency]
    else:
        raise ValueError(f"Unknown frequency: {frequency}")

    return next_deadline


def _parent_province_id(province):
    if province.parent_id is not None:
        return province.parent.province_id
    return province.province_id


def _canonical_order(order, phase_type):
    # Django/godip use a Move order in a retreat phase to mean a retreat;
    # the canonical adjudicator has a distinct Retreat order type. Django's
    # MoveViaConvoy collapses to a Move with viaConvoy set.
    via_convoy = False
    if phase_type == PhaseType.RETREAT:
        order_type = "Retreat" if order.order_type == OrderType.MOVE else order.order_type
    elif order.order_type == OrderType.MOVE_VIA_CONVOY:
        order_type = OrderType.MOVE
        via_convoy = True
    else:
        order_type = order.order_type

    source = order.source.province_id if order.source_id is not None else None
    target = order.target.province_id if order.target_id is not None else None
    aux = order.aux.province_id if order.aux_id is not None else None

    # A named coast addresses the build location for builds and the
    # destination for moves.
    if order.named_coast_id is not None:
        if order.order_type == OrderType.BUILD:
            source = order.named_coast.province_id
        else:
            target = order.named_coast.province_id

    return {
        "nation": order.nation.nation_id,
        "source": source,
        "orderType": order_type,
        "target": target,
        "aux": aux,
        "unitType": order.unit_type,
        "viaConvoy": via_convoy,
    }


def compute_province_nations(supply_centers, provinces, dominance_rules, nations):
    sc_owner_map = {sc.province.province_id: sc.nation.name for sc in supply_centers}
    province_map = {p.province_id: p for p in provinces}
    nation_id_to_name = {n.nation_id: n.name for n in nations}

    rules_by_province = {}
    for rule in dominance_rules:
        rules_by_province.setdefault(rule["province"], []).append(rule)

    UNOWNED_MARKERS = {"Empty", "Neutral"}

    def resolve_to_sc_id(province_id):
        p = province_map.get(province_id)
        if not p:
            return None
        if p.supply_center:
            return province_id
        if p.parent_id:
            parent = province_map.get(p.parent.province_id)
            if parent and parent.supply_center:
                return p.parent.province_id
        return None

    def dependency_matches(dep):
        nation = dep["nation"]
        prov = dep["province"]
        if nation in UNOWNED_MARKERS:
            return prov not in sc_owner_map
        nation_name = nation_id_to_name.get(nation)
        if not nation_name:
            return False
        return sc_owner_map.get(prov) == nation_name

    def default_color(province):
        adjacent_sc_ids = set()
        for adj in province.adjacencies:
            sc_id = resolve_to_sc_id(adj["to"])
            if sc_id:
                adjacent_sc_ids.add(sc_id)
        if not adjacent_sc_ids:
            return None
        owner = None
        for sc_id in adjacent_sc_ids:
            sc_owner = sc_owner_map.get(sc_id)
            if not sc_owner:
                return None
            if owner is None:
                owner = sc_owner
            elif owner != sc_owner:
                return None
        return owner

    result = {}
    for province in province_map.values():
        if province.supply_center:
            continue
        if province.type in (ProvinceType.SEA, ProvinceType.NAMED_COAST):
            continue

        rules = rules_by_province.get(province.province_id)
        if rules:
            matched = next((r for r in rules if all(dependency_matches(d) for d in r["dependencies"])), None)
            if matched:
                nation_name = nation_id_to_name.get(matched["nation"])
                if nation_name:
                    result[province.province_id] = nation_name
                continue

        nation_name = default_color(province)
        if nation_name:
            result[province.province_id] = nation_name

    return result


def phase_to_canonical_game_state(phase):
    phase = type(phase).objects.with_canonical_state_data().get(pk=phase.pk)
    return {
        "phase": {
            "season": phase.season,
            "year": phase.year,
            "type": phase.type,
        },
        "units": [
            {
                "nation": unit.nation.nation_id,
                "type": unit.type,
                "location": unit.province.province_id,
                "dislodged": unit.dislodged,
                "dislodgedFrom": (
                    _parent_province_id(unit.dislodged_by.province)
                    if unit.dislodged_by_id is not None
                    else None
                ),
            }
            for unit in phase.units.all()
        ],
        "supplyCenters": [
            {
                "nation": supply_center.nation.nation_id,
                "province": supply_center.province.province_id,
            }
            for supply_center in phase.supply_centers.all()
        ],
        "orders": [
            _canonical_order(order, phase.type)
            for phase_state in phase.phase_states.all()
            for order in phase_state.orders.all()
        ],
    }
