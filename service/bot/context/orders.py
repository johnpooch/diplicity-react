import logging

from common.constants import OrderType

from bot.types import OrderOptionDict

logger = logging.getLogger(__name__)


def order_option_label(option: OrderOptionDict) -> str:
    parts = [option["source"]["id"], option["order_type"]["id"]]
    for key in ("aux", "target", "unit_type", "named_coast"):
        value = option.get(key)
        if value:
            parts.append(value["id"])
    return " ".join(parts)


def option_to_selected(option: OrderOptionDict) -> list[str]:
    order_type = option["order_type"]["id"]
    selected = [option["source"]["id"], order_type]

    if order_type == OrderType.BUILD:
        selected.append(option["unit_type"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
        selected.append(option["target"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.SUPPORT, OrderType.CONVOY):
        selected.append(option["aux"]["id"])
        selected.append(option["target"]["id"])

    return selected


def group_options_by_source(
    options: list[OrderOptionDict],
) -> dict[str, list[OrderOptionDict]]:
    grouped: dict[str, list[OrderOptionDict]] = {}
    for option in options:
        grouped.setdefault(option["source"]["id"], []).append(option)
    return grouped


def first_legal_selections(options: list[OrderOptionDict]) -> list[list[str]]:
    first_by_source: dict[str, list[str]] = {}
    for option in options:
        source_id = option["source"]["id"]
        if source_id not in first_by_source:
            first_by_source[source_id] = option_to_selected(option)
    return list(first_by_source.values())
