from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr

from harness.tasks.select_orders.options import describe_option, same_option
from harness.tasks.select_orders.scorers._resolve import resolve_orders


def _ranked(state, key: str) -> list | None:
    ranked_options = (state.metadata or {}).get("ranked_options")
    if not ranked_options:
        return None
    return ranked_options.get(key) or None


@scorer(metrics=[accuracy(), stderr()])
def quality_strong():
    async def score(state, target: Target) -> Score:
        good = _ranked(state, "good")
        if good is None:
            return Score.unscored(explanation="fixture declares no strong orders")

        orders, context, failure = resolve_orders(state)
        if failure is not None:
            return failure

        found = [order for order in orders if any(same_option(order, option) for option in good)]
        return Score(
            value=CORRECT if found else INCORRECT,
            answer=state.output.completion,
            explanation=(
                f"found strong order(s): {[describe_option(order, context) for order in found]}"
                if found
                else f"no strong order; selected {[describe_option(order, context) for order in orders]}"
            ),
        )

    return score


@scorer(metrics=[accuracy(), stderr()])
def quality_avoidance():
    async def score(state, target: Target) -> Score:
        bad = _ranked(state, "bad")
        if bad is None:
            return Score.unscored(explanation="fixture declares no weak orders")

        orders, context, failure = resolve_orders(state)
        if failure is not None:
            return failure

        hit = [order for order in orders if any(same_option(order, option) for option in bad)]
        return Score(
            value=INCORRECT if hit else CORRECT,
            answer=state.output.completion,
            explanation=(
                f"selected weak order(s): {[describe_option(order, context) for order in hit]}"
                if hit
                else "avoided all weak orders"
            ),
        )

    return score
