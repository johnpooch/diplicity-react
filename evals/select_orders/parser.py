from select_orders.exceptions import ParsingError
from select_orders.options import option_id
from select_orders.types import Context, OrderOption
from select_orders.utils import parse_json_object


def parse_completion(completion: str, context: Context) -> list[OrderOption]:
    data = parse_json_object(completion)

    choices = data.get("choices")
    if not isinstance(choices, list):
        raise ParsingError("response has no 'choices' list")

    options_by_id = {option_id(option): option for option in context["order_options"]}
    selected: list[OrderOption] = []
    for choice in choices:
        chosen_id = choice.get("option_id") if isinstance(choice, dict) else None
        if not isinstance(chosen_id, str):
            raise ParsingError(f"choice has no string 'option_id': {choice!r}")
        if chosen_id not in options_by_id:
            raise ParsingError(f"unknown option id '{chosen_id}'")
        selected.append(options_by_id[chosen_id])

    return selected
