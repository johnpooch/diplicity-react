import json
import random

from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset
from inspect_ai.model import ModelOutput
from inspect_ai.solver import solver

from harness.tasks.select_orders.evals import DATASET_PATH, fixture_to_sample
from harness.tasks.select_orders.options import group_options_by_source, same_option
from harness.tasks.select_orders.scorers import (
    convoy_coherence,
    coverage,
    deduplication,
    legality,
    quality_avoidance,
    quality_strong,
    support_coherence,
)

from dumbbot.policy import select_orders


@solver
def dumbbot_solver():
    async def solve(state, generate):
        context = state.metadata["context"]
        orders = select_orders(context, rng=random.Random(state.epoch))
        grouped = group_options_by_source(context["order_options"])
        choices = []
        for order in orders:
            options = grouped[order["source"]]
            index = next(i for i, option in enumerate(options) if same_option(option, order))
            choices.append({"source_id": order["source"], "option_index": index})
        state.output = ModelOutput.from_content(model="dumbbot", content=json.dumps({"choices": choices}))
        return state

    return solve


@task
def dumbbot_select_orders():
    return Task(
        dataset=json_dataset(str(DATASET_PATH), fixture_to_sample),
        solver=dumbbot_solver(),
        scorer=[
            legality(),
            deduplication(),
            coverage(),
            support_coherence(),
            convoy_coherence(),
            quality_strong(),
            quality_avoidance(),
        ],
    )
