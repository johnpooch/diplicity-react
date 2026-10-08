import json
import random

from inspect_ai.model import ModelOutput
from inspect_ai.solver import solver

from dumbbot.policy import select_orders as dumbbot_select_orders
from select_orders.options import option_id


@solver
def dumbbot_solver():
    async def solve(state, generate):
        context = state.metadata["context"]
        orders = dumbbot_select_orders(context, rng=random.Random(state.epoch))
        choices = [{"option_id": option_id(order)} for order in orders]
        state.output = ModelOutput.from_content(model="dumbbot", content=json.dumps({"choices": choices}))
        return state

    return solve
