from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import generate

from harness.adapter import fixture_to_context
from harness.tasks.select_orders.scorers import (
    convoy_coherence,
    coverage,
    deduplication,
    legality,
    quality_avoidance,
    quality_strong,
    support_coherence,
)
from harness.tasks.select_orders.system_prompt import system_prompt
from harness.tasks.select_orders.user_prompt import user_prompt
from harness.types import SelectOrdersFixture

DATASET_PATH = Path(__file__).with_name("dataset.json")


def fixture_to_sample(record: dict) -> Sample:
    fixture: SelectOrdersFixture = record
    context = fixture_to_context(fixture)
    return Sample(
        id=fixture["id"],
        input=[
            ChatMessageSystem(content=system_prompt(context)),
            ChatMessageUser(content=user_prompt(context)),
        ],
        metadata={
            "context": context,
            "notes": fixture.get("notes", ""),
            "ranked_options": fixture.get("ranked_options"),
        },
    )


@task
def select_orders():
    return Task(
        dataset=json_dataset(str(DATASET_PATH), fixture_to_sample),
        solver=generate(),
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
