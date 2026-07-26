from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr

from harness_v2.tasks.select_orders.options import describe_option, same_option
from harness_v2.tasks.select_orders.scorers._resolve import resolve_orders


@scorer(metrics=[accuracy(), stderr()])
def legality():
    async def score(state, target: Target) -> Score:
        orders, context, failure = resolve_orders(state)
        if failure is not None:
            return failure

        legal = context["order_options"]
        illegal = [order for order in orders if not any(same_option(order, option) for option in legal)]

        return Score(
            value=INCORRECT if illegal else CORRECT,
            answer=state.output.completion,
            explanation=(
                f"illegal orders: {[describe_option(order, context) for order in illegal]}"
                if illegal
                else f"all {len(orders)} order(s) legal"
            ),
        )

    return score
