from inspect_ai.scorer import INCORRECT, Score

from harness.exceptions import ParsingError
from harness.tasks.select_orders.parser import parse_completion
from harness.types import Context, OrderOption


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
