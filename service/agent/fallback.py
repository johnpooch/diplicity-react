from harness_v2.types import OrderOption


def first_legal_options(options: list[OrderOption]) -> list[OrderOption]:
    first_by_source: dict[str, OrderOption] = {}
    for option in options:
        if option["source"] not in first_by_source:
            first_by_source[option["source"]] = option
    return list(first_by_source.values())
