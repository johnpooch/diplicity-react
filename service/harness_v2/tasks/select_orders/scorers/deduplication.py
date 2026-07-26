from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr

from harness_v2.tasks.select_orders.scorers._resolve import resolve_orders


@scorer(metrics=[accuracy(), stderr()])
def deduplication():
    async def score(state, target: Target) -> Score:
        orders, _, failure = resolve_orders(state)
        if failure is not None:
            return failure

        sources = [order["source"] for order in orders]
        duplicated = sorted({source for source in sources if sources.count(source) > 1})

        return Score(
            value=INCORRECT if duplicated else CORRECT,
            answer=state.output.completion,
            explanation=(
                f"provinces ordered more than once: {duplicated}"
                if duplicated
                else f"{len(sources)} province(s), no duplicates"
            ),
        )

    return score
