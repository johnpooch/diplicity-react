from common.constants import OrderType


def _navigate_options(current_options, key, error_message):
    if key not in current_options:
        raise ValueError(error_message)
    return current_options[key].get("Next", {})


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

        if order.source.province_id in current_options:
            current_options = current_options[order.source.province_id].get("Next", {})

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
