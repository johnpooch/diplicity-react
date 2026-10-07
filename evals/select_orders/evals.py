from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import generate

from select_orders.context import fixture_to_context
from select_orders.dumbbot_solver import dumbbot_solver
from select_orders.exceptions import FixtureError
from select_orders.fixtures import foreign_orders, ranked_options, read_fixture
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


def load_fixtures(eval_set: str | None = None) -> list[Fixture]:
    fixtures = [read_fixture(path) for path in sorted(FIXTURES_DIR.glob("*.json"))]
    if eval_set is None:
        return fixtures
    members = [fixture for fixture in fixtures if eval_set in fixture["eval_sets"]]
    if not members:
        raise FixtureError(f"eval set '{eval_set}' has no fixtures")
    return members


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
            "ranked_options": ranked_options(fixture),
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


def _dataset(eval_set: str | None = None) -> MemoryDataset:
    return MemoryDataset([fixture_to_sample(fixture) for fixture in load_fixtures(eval_set)])


@task
def select_orders(eval_set: str | None = None):
    return Task(dataset=_dataset(eval_set), solver=generate(), scorer=_scorers())


@task
def dumbbot_select_orders():
    return Task(dataset=_dataset(), solver=dumbbot_solver(), scorer=_scorers())
