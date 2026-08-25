import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from agent import tasks
from common.constants import DeadlineMode, GameStatus, MovementPhaseDuration, PhaseType, UserKind
from game.models import Game
from integration.scoring import sum_of_squares
from user_profile.models import UserProfile

pytestmark = pytest.mark.skipif(
    not settings.BOT_ANTHROPIC_API_KEY,
    reason="the dumbbot match plays real LLM games and needs BOT_ANTHROPIC_API_KEY",
)

TARGET_SEASON = "Spring"
TARGET_YEAR = 1910
MAX_PHASES = 120


@pytest.fixture
def game_master_client(authenticated_client, primary_user, settings):
    settings.BOT_OPPONENT_ALLOWLIST = [primary_user.email.lower()]
    return authenticated_client


def _create_match_game(client, variant_id, name, llm_seats, dumbbot_seats):
    response = client.post(
        reverse("game-create"),
        {
            "name": name,
            "variant_id": variant_id,
            "private": True,
            "game_master": True,
            "deadline_mode": DeadlineMode.DURATION,
            "movement_phase_duration": MovementPhaseDuration.TWENTY_FOUR_HOURS,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    game = Game.objects.get(id=response.data["id"])

    available = UserProfile.objects.addable_to_game(game)
    profiles = list(available.filter(kind=UserKind.LLM)[:llm_seats])
    profiles += list(available.filter(kind=UserKind.DUMBBOT)[:dumbbot_seats])
    assert len(profiles) == llm_seats + dumbbot_seats

    for profile in profiles:
        add_response = client.post(
            reverse("game-member-create", args=[game.id]), {"user_id": profile.user_id}, format="json"
        )
        assert add_response.status_code == status.HTTP_201_CREATED

    game.refresh_from_db()
    assert game.status == GameStatus.ACTIVE
    return game


def _at_target(phase):
    return phase.season == TARGET_SEASON and phase.year == TARGET_YEAR and phase.type == PhaseType.MOVEMENT


def _drive_to_target(client, game):
    for _ in range(MAX_PHASES):
        game.refresh_from_db()
        if game.status != GameStatus.ACTIVE:
            return f"game ended early with status {game.status}"
        phase = game.current_phase
        if _at_target(phase):
            return "reached target"

        phase_states = phase.phase_states.filter(has_possible_orders=True).select_related("member")
        for phase_state in phase_states.order_by("member_id"):
            tasks.finalize(user_id=phase_state.member.user_id, game_id=game.id)

        response = client.post(reverse("phase-resolve-all"))
        assert response.status_code == status.HTTP_200_OK

        game.refresh_from_db()
        if game.status == GameStatus.ACTIVE:
            assert game.current_phase.id != phase.id, (
                f"phase did not advance: {phase.season} {phase.year} {phase.type}"
            )

        score = sum_of_squares(game.current_phase)
        print(
            f"{game.name}: {game.current_phase.season} {game.current_phase.year} "
            f"{game.current_phase.type} centers={score.centers}"
        )
    pytest.fail(f"{game.name}: hit the {MAX_PHASES}-phase cap without reaching the target")


def _report(game, outcome):
    score = sum_of_squares(game.current_phase)
    print(f"\n=== {game.name} ({outcome}; model={settings.BOT_LLM_MODEL}) ===")
    for nation in sorted(score.centers):
        print(
            f"{nation:>10} [{score.kinds.get(nation, 'human'):>7}] "
            f"centers={score.centers[nation]:>2} score={score.scores[nation]:>3}"
        )
    print(f"cohorts={score.cohorts} total={score.total}")
    return score


def _assert_invariants(game, score):
    total_owned = sum(score.centers.values())
    assert all(count >= 0 for count in score.centers.values())
    assert total_owned <= game.variant.provinces.filter(supply_center=True).count()
    assert score.total > 0


@pytest.mark.django_db
def test_llm_majority_versus_one_dumbbot(game_master_client, classical_variant):
    game = _create_match_game(
        game_master_client, classical_variant.id, "Match A: 6 LLM + 1 dumbbot", llm_seats=6, dumbbot_seats=1
    )
    outcome = _drive_to_target(game_master_client, game)
    score = _report(game, outcome)
    _assert_invariants(game, score)


@pytest.mark.django_db
def test_dumbbot_majority_versus_one_llm(game_master_client, classical_variant):
    game = _create_match_game(
        game_master_client, classical_variant.id, "Match B: 1 LLM + 6 dumbbots", llm_seats=1, dumbbot_seats=6
    )
    outcome = _drive_to_target(game_master_client, game)
    score = _report(game, outcome)
    _assert_invariants(game, score)
