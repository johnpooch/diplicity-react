from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr

from harness.tasks.select_orders.scorers._resolve import resolve_orders
from harness.types import OrderOption

MOVEMENT_TYPES = {"Move", "MoveViaConvoy"}


def destinations(orders: list[OrderOption]) -> dict[str, str | None]:
    resolved: dict[str, str | None] = {}
    for order in orders:
        source = order["source"]
        if order["order_type"] in MOVEMENT_TYPES:
            resolved[source] = order["target"]
        else:
            resolved[source] = source
    return resolved


def dangling(orders: list[OrderOption], order_type: str) -> list[tuple[str, str, str | None]]:
    resolved = destinations(orders)
    broken = []
    for order in orders:
        if order["order_type"] != order_type:
            continue
        aux = order["aux"]
        target = order["target"]
        if aux is None or target is None:
            continue
        if resolved.get(aux) != target:
            broken.append((aux, target, resolved.get(aux)))
    return broken


@scorer(metrics=[accuracy(), stderr()])
def support_coherence():
    async def score(state, target: Target) -> Score:
        orders, _, failure = resolve_orders(state)
        if failure is not None:
            return failure

        broken = dangling(orders, "Support")
        return Score(
            value=INCORRECT if broken else CORRECT,
            answer=state.output.completion,
            explanation=(
                f"dangling supports (aux, target, aux_actual_destination): {broken}"
                if broken
                else "all supports coherent"
            ),
        )

    return score


@scorer(metrics=[accuracy(), stderr()])
def convoy_coherence():
    async def score(state, target: Target) -> Score:
        orders, _, failure = resolve_orders(state)
        if failure is not None:
            return failure

        broken = dangling(orders, "Convoy")
        return Score(
            value=INCORRECT if broken else CORRECT,
            answer=state.output.completion,
            explanation=(
                f"dangling convoys (army, target, army_actual_destination): {broken}"
                if broken
                else "all convoys coherent"
            ),
        )

    return score
