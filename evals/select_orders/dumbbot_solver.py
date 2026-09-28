import json
import random

from inspect_ai.model import ModelOutput
from inspect_ai.solver import solver

from dumbbot.policy import select_orders as dumbbot_select_orders
from select_orders.options import group_options_by_source, same_option


@solver
def dumbbot_solver():
    async def solve(state, generate):
        context = state.metadata["context"]
        orders = dumbbot_select_orders(context, rng=random.Random(state.epoch))
        grouped = group_options_by_source(context["order_options"])
        choices = []
        for order in orders:
            options = grouped[order["source"]]
            index = next(i for i, option in enumerate(options) if same_option(option, order))
            choices.append({"source_id": order["source"], "option_index": index})
        state.output = ModelOutput.from_content(model="dumbbot", content=json.dumps({"choices": choices}))
        return state

    return solve
