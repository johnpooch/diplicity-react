from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr

from harness_v2.tasks.select_orders.options import group_options_by_source
from harness_v2.tasks.select_orders.scorers._resolve import resolve_orders


@scorer(metrics=[accuracy(), stderr()])
def coverage():
    async def score(state, target: Target) -> Score:
        orders, context, failure = resolve_orders(state)
        if failure is not None:
            return failure

        orderable = set(group_options_by_source(context["order_options"]))
        covered = {order["source"] for order in orders}
        max_orders = context.get("max_orders")

        if max_orders is None:
            missing = sorted(orderable - covered)
            return Score(
                value=INCORRECT if missing else CORRECT,
                answer=state.output.completion,
                explanation=(
                    f"provinces with no order: {missing} ({len(covered)}/{len(orderable)} covered)"
                    if missing
                    else f"all {len(orderable)} province(s) covered"
                ),
            )

        expected = min(max_orders, len(orderable))
        return Score(
            value=CORRECT if len(covered) == expected else INCORRECT,
            answer=state.output.completion,
            explanation=f"submitted {len(covered)} order(s), expected exactly {expected} (max_orders={max_orders})",
        )

    return score
