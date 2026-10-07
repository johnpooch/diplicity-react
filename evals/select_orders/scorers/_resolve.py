from inspect_ai.scorer import INCORRECT, Score

from select_orders.exceptions import ParsingError
from select_orders.parser import parse_completion
from select_orders.types import Context, OrderOption


def resolve_orders(state) -> tuple[list[OrderOption], Context, Score | None]:
    context = state.metadata["context"]
    try:
        orders = parse_completion(state.output.completion, context)
    except ParsingError as e:
        failure = Score(
            value=INCORRECT,
            answer=state.output.completion,
            explanation=f"unparseable completion: {e}",
        )
        return [], context, failure
    return orders, context, None
