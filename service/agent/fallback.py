from harness.orders import option_to_selected
from harness.types import OrderOptionDict


def first_legal_selections(options: list[OrderOptionDict]) -> list[list[str]]:
    first_by_source: dict[str, list[str]] = {}
    for option in options:
        source_id = option["source"]["id"]
        if source_id not in first_by_source:
            first_by_source[source_id] = option_to_selected(option)
    return list(first_by_source.values())
