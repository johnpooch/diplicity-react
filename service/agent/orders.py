from common.constants import OrderType

from harness_v2.types import OrderOption


def option_to_selected(option: OrderOption) -> list[str]:
    order_type = option["order_type"]
    selected = [option["source"], order_type]

    if order_type == OrderType.BUILD:
        selected.append(option["unit_type"])
        if option["named_coast"]:
            selected.append(option["named_coast"])
    elif order_type in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
        selected.append(option["target"])
        if option["named_coast"]:
            selected.append(option["named_coast"])
    elif order_type in (OrderType.SUPPORT, OrderType.CONVOY):
        selected.append(option["aux"])
        selected.append(option["target"])

    return selected
