from select_orders.exceptions import FixtureError
from select_orders.types import Context, OrderOption


def group_options_by_source(order_options: list[OrderOption]) -> dict[str, list[OrderOption]]:
    grouped: dict[str, list[OrderOption]] = {}
    for option in order_options:
        grouped.setdefault(option["source"], []).append(option)
    return grouped


def _names(context: Context) -> dict[str, str]:
    return {province["id"]: province["name"] for province in context["provinces"]}


def describe_option(option: OrderOption, context: Context) -> str:
    names = _names(context)
    label = option["order_type"]
    if option["unit_type"]:
        label += f" {option['unit_type']}"
    if option["aux"]:
        label += f" {names.get(option['aux'], option['aux'])}"
    target = option["target"]
    if target is not None and target != option["source"] and target != option["aux"]:
        label += f" -> {names.get(target, target)}"
    if option["named_coast"]:
        label += f" ({names.get(option['named_coast'], option['named_coast'])})"
    return label


OPTION_KEYS = ("source", "order_type", "target", "aux", "unit_type", "named_coast")


def same_option(left: OrderOption, right: OrderOption) -> bool:
    return all(left.get(key) == right.get(key) for key in OPTION_KEYS)


def option_id(option: OrderOption) -> str:
    return ":".join(option.get(key) or "" for key in OPTION_KEYS).rstrip(":")


def option_from_id(value: str) -> OrderOption:
    parts = value.split(":")
    if len(parts) > len(OPTION_KEYS) or len(parts) < 2 or not parts[0] or not parts[1]:
        raise FixtureError(f"malformed option id '{value}'")
    padded = parts + [""] * (len(OPTION_KEYS) - len(parts))
    return {key: part or None for key, part in zip(OPTION_KEYS, padded)}
