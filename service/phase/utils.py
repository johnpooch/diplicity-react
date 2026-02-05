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


def calculate_next_fixed_deadline(
    target_time,
    frequency,
    tz_name,
    reference_time=None,
):
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    from django.utils import timezone

    from common.constants import PhaseFrequency

    if reference_time is None:
        reference_time = timezone.now()

    tz = ZoneInfo(tz_name)
    local_now = reference_time.astimezone(tz)

    if frequency == PhaseFrequency.HOURLY:
        next_deadline = local_now.replace(minute=0, second=0, microsecond=0)
        next_deadline += timedelta(hours=1)
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
    else:
        raise ValueError(f"Unknown frequency: {frequency}")

    return next_deadline
