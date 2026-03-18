from common.constants import OrderType

FIELD_ORDER = {
    "Hold": ["source", "orderType"],
    "Disband": ["source", "orderType"],
    "Move": ["source", "orderType", "target", "namedCoast"],
    "MoveViaConvoy": ["source", "orderType", "target"],
    "Support": ["source", "orderType", "aux", "target"],
    "Convoy": ["source", "orderType", "aux", "target"],
    "Build": ["source", "orderType", "unitType", "namedCoast"],
}


def _make_field_value(id, province_lookup):
    province = province_lookup.get(id)
    return {"id": id, "label": province.name if province else id}


def _is_named_coast_dict(d):
    return bool(d) and all("/" in k for k in d)


def flatten_options(nation_options, province_lookup):
    results = []

    for source_id, order_types in nation_options.items():
        source = _make_field_value(source_id, province_lookup)

        for order_type_id, order_type_data in order_types.items():
            order_type = {"id": order_type_id, "label": order_type_id}

            if order_type_id in (OrderType.HOLD, OrderType.DISBAND):
                results.append({
                    "source": source,
                    "orderType": order_type,
                    "target": None,
                    "aux": None,
                    "unitType": None,
                    "namedCoast": None,
                })

            elif order_type_id in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
                for target_id, target_data in order_type_data.items():
                    target = _make_field_value(target_id, province_lookup)
                    if _is_named_coast_dict(target_data):
                        for coast_id in target_data:
                            results.append({
                                "source": source,
                                "orderType": order_type,
                                "target": target,
                                "aux": None,
                                "unitType": None,
                                "namedCoast": _make_field_value(coast_id, province_lookup),
                            })
                    else:
                        results.append({
                            "source": source,
                            "orderType": order_type,
                            "target": target,
                            "aux": None,
                            "unitType": None,
                            "namedCoast": None,
                        })

            elif order_type_id in (OrderType.SUPPORT, OrderType.CONVOY):
                for aux_id, aux_data in order_type_data.items():
                    aux = _make_field_value(aux_id, province_lookup)
                    for target_id in aux_data:
                        results.append({
                            "source": source,
                            "orderType": order_type,
                            "target": _make_field_value(target_id, province_lookup),
                            "aux": aux,
                            "unitType": None,
                            "namedCoast": None,
                        })

            elif order_type_id == OrderType.BUILD:
                for unit_type_id, unit_type_data in order_type_data.items():
                    unit_type = {"id": unit_type_id, "label": unit_type_id}
                    if _is_named_coast_dict(unit_type_data):
                        for coast_id in unit_type_data:
                            results.append({
                                "source": source,
                                "orderType": order_type,
                                "target": None,
                                "aux": None,
                                "unitType": unit_type,
                                "namedCoast": _make_field_value(coast_id, province_lookup),
                            })
                    else:
                        results.append({
                            "source": source,
                            "orderType": order_type,
                            "target": None,
                            "aux": None,
                            "unitType": unit_type,
                            "namedCoast": None,
                        })

    return results


def get_order_data_from_selected(selected):
    if not selected:
        return {}

    result = {}
    result["source"] = selected[0]

    if len(selected) <= 1:
        return result

    result["order_type"] = selected[1]

    if result["order_type"] == OrderType.BUILD:
        if len(selected) >= 3:
            result["unit_type"] = selected[2]
        if len(selected) >= 4:
            result["named_coast"] = selected[3]
    elif result["order_type"] in [OrderType.MOVE, OrderType.MOVE_VIA_CONVOY]:
        if len(selected) >= 3:
            result["target"] = selected[2]
        if len(selected) >= 4:
            result["named_coast"] = selected[3]
    elif result["order_type"] == OrderType.SUPPORT:
        if len(selected) >= 3:
            result["aux"] = selected[2]
        if len(selected) >= 4:
            result["target"] = selected[3]
    elif result["order_type"] == OrderType.CONVOY:
        if len(selected) >= 3:
            result["aux"] = selected[2]
        if len(selected) >= 4:
            result["target"] = selected[3]

    return result


def _navigate_options(current_options, key, error_message):
    if key not in current_options:
        raise ValueError(error_message)
    return current_options[key]


def get_options_for_order(options, order):
    current_options = options[order.nation.name]

    if not order.source:
        return list(current_options.keys())

    current_options = _navigate_options(
        current_options, order.source.province_id, f"Source province {order.source.province_id} not found in options"
    )

    if order.order_type:
        current_options = _navigate_options(
            current_options, order.order_type, f"Order type {order.order_type} not found in options"
        )

    if order.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
        if order.aux:
            current_options = _navigate_options(
                current_options,
                order.aux.province_id,
                f"Auxiliary province {order.aux.province_id} not found in options",
            )

            if order.target:
                if order.target.province_id not in current_options:
                    raise ValueError(f"Target province {order.target.province_id} not found in options")
                return []
    else:
        if order.target:
            current_options = _navigate_options(
                current_options,
                order.target.province_id,
                f"Target province {order.target.province_id} not found in options",
            )

    if order.order_type == OrderType.BUILD and order.unit_type:
        current_options = _navigate_options(
            current_options, order.unit_type, f"Unit type {order.unit_type} not found in options"
        )

    if order.order_type not in [OrderType.SUPPORT, OrderType.CONVOY] and order.aux:
        current_options = _navigate_options(
            current_options, order.aux.province_id, f"Auxiliary province {order.aux.province_id} not found in options"
        )

    return list(current_options.keys())
