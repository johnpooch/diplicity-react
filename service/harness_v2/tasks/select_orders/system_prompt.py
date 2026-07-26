from common.constants import PhaseType

from harness_v2.types import Context

ROLE = """You are an expert Diplomacy player. You will be given the state of a game and \
the complete list of legal orders available to you this phase, grouped by the province \
that issues them."""

MOVEMENT_TASK = """Select exactly one order for every province listed. A province with no \
order does nothing, which is almost always worse than the weakest listed alternative."""

RETREAT_TASK = """Each province listed holds a dislodged unit that must be dealt with this \
phase. Select exactly one order for every province listed. A unit given no order is \
destroyed."""

ADJUSTMENT_TASK = """You may not order every province listed. Select orders for exactly \
{max_orders} of them and leave the rest alone, choosing the {max_orders} that most improve \
your position."""

ADJUSTMENT_TASK_UNKNOWN = """You may not order every province listed. Select orders only for \
the provinces you are entitled to adjust this phase, and leave the rest alone."""

FORMAT = """Respond with JSON only. No markdown fences, no prose outside the JSON. Use this \
shape:

{"reasoning": "<brief explanation of your plan>", "choices": [{"source_id": "<province id>", "option_index": <number>}]}

The option_index is the number shown beside the order in that province's own list. Indices \
restart at 0 for every province. Give at most one entry per province."""


def task_instruction(context: Context) -> str:
    phase_type = context["phase"]["type"]
    if phase_type == PhaseType.ADJUSTMENT:
        max_orders = context.get("max_orders")
        if max_orders is None:
            return ADJUSTMENT_TASK_UNKNOWN
        return ADJUSTMENT_TASK.format(max_orders=max_orders)
    if phase_type == PhaseType.RETREAT:
        return RETREAT_TASK
    return MOVEMENT_TASK


def system_prompt(context: Context) -> str:
    return "\n\n".join([ROLE, task_instruction(context), FORMAT])
