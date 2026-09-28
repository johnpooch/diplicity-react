from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import generate

from select_orders.context import fixture_to_context
from select_orders.dumbbot_solver import dumbbot_solver
from select_orders.fixtures import foreign_orders, read_fixture
from select_orders.scorers import (
    convoy_coherence,
    coverage,
    deduplication,
    legality,
    quality_avoidance,
    quality_strong,
    support_coherence,
)
from select_orders.prompt import system_prompt, user_prompt
from select_orders.types import Fixture

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixtures() -> list[Fixture]:
    return [read_fixture(path) for path in sorted(FIXTURES_DIR.glob("*.json"))]


def fixture_to_sample(fixture: Fixture) -> Sample:
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
            "foreign_orders": foreign_orders(fixture),
        },
    )


def _scorers():
    return [
        legality(),
        deduplication(),
        coverage(),
        support_coherence(),
        convoy_coherence(),
        quality_strong(),
        quality_avoidance(),
    ]


def _dataset() -> MemoryDataset:
    return MemoryDataset([fixture_to_sample(fixture) for fixture in load_fixtures()])


@task
def select_orders():
    return Task(dataset=_dataset(), solver=generate(), scorer=_scorers())


@task
def dumbbot_select_orders():
    return Task(dataset=_dataset(), solver=dumbbot_solver(), scorer=_scorers())
