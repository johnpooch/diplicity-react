from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import generate

from select_orders.context import fixture_to_context
from select_orders.dumbbot_solver import dumbbot_solver
from select_orders.exceptions import FixtureError, PromptError
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
from select_orders.prompt import check_option_ids, system_prompt, user_prompt
from select_orders.types import Fixture

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_fixtures(eval_set: str | None = None) -> list[Fixture]:
    fixtures = [read_fixture(path) for path in sorted(FIXTURES_DIR.glob("*.json"))]
    if eval_set is None:
        return fixtures
    members = [fixture for fixture in fixtures if eval_set in fixture["eval_sets"]]
    if not members:
        raise FixtureError(f"eval set '{eval_set}' has no fixtures")
    return members


def select_fixtures(
    eval_set: str | None = None, fixture_id: str | None = None
) -> list[Fixture]:
    fixtures = load_fixtures(eval_set)
    if fixture_id is None:
        return fixtures
    selected = [fixture for fixture in fixtures if fixture["id"] == fixture_id]
    if not selected:
        raise FixtureError(f"fixture '{fixture_id}' is not in eval set '{eval_set}'")
    return selected


def fixture_to_sample(
    fixture: Fixture, system: str | None = None, user: str | None = None
) -> Sample:
    context = fixture_to_context(fixture)
    if user is not None:
        check_option_ids(user, context)
    return Sample(
        id=fixture["id"],
        input=[
            ChatMessageSystem(
                content=system_prompt(context) if system is None else system
            ),
            ChatMessageUser(content=user_prompt(context) if user is None else user),
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


def _read_prompt(path: str | None) -> str | None:
    return None if path is None else Path(path).read_text()


def variant_path(fixture_id: str, variant: str) -> Path:
    return PROMPTS_DIR / fixture_id / f"{variant}.txt"


def _variant_prompt(fixture: Fixture, variant: str | None) -> str | None:
    if variant is None:
        return None
    path = variant_path(fixture["id"], variant)
    if not path.is_file():
        raise PromptError(
            f"fixture '{fixture['id']}' has no '{variant}' prompt at {path}; run build_prompts"
        )
    return path.read_text()


def _dataset(
    eval_set: str | None = None,
    fixture_id: str | None = None,
    system_file: str | None = None,
    user_file: str | None = None,
    user_variant: str | None = None,
) -> MemoryDataset:
    if (system_file or user_file) and fixture_id is None:
        raise FixtureError(
            "a custom prompt is written for one fixture; name it with --fixture"
        )
    if user_file and user_variant:
        raise PromptError("pass a user prompt file or a user prompt variant, not both")
    fixtures = select_fixtures(eval_set, fixture_id)
    system, user = _read_prompt(system_file), _read_prompt(user_file)
    return MemoryDataset(
        [
            fixture_to_sample(
                fixture, system, user or _variant_prompt(fixture, user_variant)
            )
            for fixture in fixtures
        ]
    )


@task
def select_orders(
    eval_set: str | None = None,
    fixture_id: str | None = None,
    system_file: str | None = None,
    user_file: str | None = None,
    user_variant: str | None = None,
):
    return Task(
        dataset=_dataset(eval_set, fixture_id, system_file, user_file, user_variant),
        solver=generate(),
        scorer=_scorers(),
    )


@task
def dumbbot_select_orders():
    return Task(dataset=_dataset(), solver=dumbbot_solver(), scorer=_scorers())
