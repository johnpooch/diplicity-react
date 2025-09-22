from common.constants import OrderType


def get_options_for_order(options, order):
    options = options[order.nation]

    current_options = options

    if not order.source:
        return list(options.keys())

    if order.source:
        source_province = order.source
        if source_province in current_options:
            current_options = current_options[source_province].get("Next", {})
        else:
            raise ValueError(f"Source province {order.source} not found in options")

    if order.order_type:
        order_type = order.order_type
        if order_type in current_options:
            current_options = current_options[order_type].get("Next", {})
        else:
            raise ValueError(f"Order type {order.order_type} not found in options")

        if order.source in current_options:
            current_options = current_options[order.source].get("Next", {})

    if order.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
        if order.aux:
            if order.aux in current_options:
                current_options = current_options[order.aux].get("Next", {})
            else:
                raise ValueError(f"Auxiliary province {order.aux} not found in options")

            if order.target:
                if order.target not in current_options:
                    raise ValueError(f"Target province {order.target} not found in options")
                return []
    else:
        if order.target:
            target_province = order.target
            if target_province in current_options:
                current_options = current_options[target_province].get("Next", {})
            else:
                raise ValueError(f"Target province {order.target} not found in options")

    if order.order_type == OrderType.BUILD and order.unit_type:
        if order.unit_type in current_options:
            current_options = current_options[order.unit_type].get("Next", {})
        else:
            raise ValueError(f"Unit type {order.unit_type} not found in options")

    if order.order_type not in [OrderType.SUPPORT, OrderType.CONVOY] and order.aux:
        aux_province = order.aux
        if aux_province in current_options:
            current_options = current_options[aux_province].get("Next", {})
        else:
            raise ValueError(f"Auxiliary province {order.aux} not found in options")

    return list(current_options.keys())
