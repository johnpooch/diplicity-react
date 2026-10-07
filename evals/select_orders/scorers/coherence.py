from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr

from select_orders.scorers._resolve import resolve_orders
from select_orders.types import Context, OrderOption

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


def foreign_units(context: Context) -> set[str]:
    own = {member["nation"] for member in context.get("members", []) if member["is_current_user"]}
    parents = {province["id"]: province["parent_id"] or province["id"] for province in context.get("provinces", [])}
    return {
        parents.get(unit["province"], unit["province"])
        for unit in context.get("units", [])
        if own and unit["nation"] not in own
    }


def dangling(
    orders: list[OrderOption],
    order_type: str,
    foreign_orders: list[OrderOption] | None = None,
    foreign: set[str] = frozenset(),
) -> list[tuple[str, str, str | None]]:
    resolved = destinations([*orders, *(foreign_orders or [])])
    if foreign_orders is not None:
        for province in foreign:
            resolved.setdefault(province, province)
    broken = []
    for order in orders:
        if order["order_type"] != order_type:
            continue
        aux = order["aux"]
        target = order["target"]
        if aux is None or target is None:
            continue
        if aux not in resolved and aux in foreign:
            continue
        if resolved.get(aux) != target:
            broken.append((aux, target, resolved.get(aux)))
    return broken


def _dangling(state, orders, context, order_type):
    return dangling(orders, order_type, (state.metadata or {}).get("foreign_orders"), foreign_units(context))


@scorer(metrics=[accuracy(), stderr()])
def support_coherence():
    async def score(state, target: Target) -> Score:
        orders, context, failure = resolve_orders(state)
        if failure is not None:
            return failure

        broken = _dangling(state, orders, context, "Support")
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
        orders, context, failure = resolve_orders(state)
        if failure is not None:
            return failure

        broken = _dangling(state, orders, context, "Convoy")
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
