from common.constants import OrderType


def _navigate_options(current_options, key, error_message):
    if key not in current_options:
        raise ValueError(error_message)
    return current_options[key].get("Next", {})


def get_options_for_order(options, order):
    current_options = options[order.nation]

    if not order.source:
        return list(current_options.keys())

    current_options = _navigate_options(
        current_options, order.source,
        f"Source province {order.source} not found in options"
    )

    if order.order_type:
        current_options = _navigate_options(
            current_options, order.order_type,
            f"Order type {order.order_type} not found in options"
        )

        if order.source in current_options:
            current_options = current_options[order.source].get("Next", {})

    if order.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
        if order.aux:
            current_options = _navigate_options(
                current_options, order.aux,
                f"Auxiliary province {order.aux} not found in options"
            )

            if order.target:
                if order.target not in current_options:
                    raise ValueError(f"Target province {order.target} not found in options")
                return []
    else:
        if order.target:
            current_options = _navigate_options(
                current_options, order.target,
                f"Target province {order.target} not found in options"
            )

    if order.order_type == OrderType.BUILD and order.unit_type:
        current_options = _navigate_options(
            current_options, order.unit_type,
            f"Unit type {order.unit_type} not found in options"
        )

    if order.order_type not in [OrderType.SUPPORT, OrderType.CONVOY] and order.aux:
        current_options = _navigate_options(
            current_options, order.aux,
            f"Auxiliary province {order.aux} not found in options"
        )

    return list(current_options.keys())
