from select_orders.exceptions import ParsingError
from select_orders.options import group_options_by_source
from select_orders.types import Context, OrderOption
from select_orders.utils import parse_json_object


def parse_completion(completion: str, context: Context) -> list[OrderOption]:
    data = parse_json_object(completion)

    choices = data.get("choices")
    if not isinstance(choices, list):
        raise ParsingError("response has no 'choices' list")

    chosen: dict[str, object] = {}
    for choice in choices:
        if isinstance(choice, dict) and "source_id" in choice and "option_index" in choice:
            chosen[choice["source_id"]] = choice["option_index"]

    selected: list[OrderOption] = []
    for source_id, options in group_options_by_source(context["order_options"]).items():
        index = chosen.get(source_id)
        if not isinstance(index, int) or isinstance(index, bool):
            continue
        if not 0 <= index < len(options):
            continue
        selected.append(options[index])

    return selected
