import random
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from agent import tasks
from common.constants import DeadlineMode, GameStatus, MovementPhaseDuration, NationAssignment, PhaseStatus, UserKind
from game.models import Game
from inference.models import Inference
from integration.scoring import sum_of_squares
from user_profile.models import UserProfile


@pytest.fixture
def game_master_client(authenticated_client, primary_user, settings):
    settings.BOT_OPPONENT_ALLOWLIST = [primary_user.email.lower()]
    return authenticated_client


def _create_game_master_game(client, variant_id):
    response = client.post(
        reverse("game-create"),
        {
            "name": "Dumbbot Integration Game",
            "variant_id": variant_id,
            "nation_assignment": NationAssignment.ORDERED,
            "private": True,
            "game_master": True,
            "deadline_mode": DeadlineMode.DURATION,
            "movement_phase_duration": MovementPhaseDuration.TWENTY_FOUR_HOURS,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return Game.objects.get(id=response.data["id"])


def _add_bots(client, game, profiles):
    for profile in profiles:
        response = client.post(
            reverse("game-member-create", args=[game.id]), {"user_id": profile.user_id}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
    game.refresh_from_db()
    return game


def _finalize_all(game):
    phase_states = game.current_phase.phase_states.filter(has_possible_orders=True).select_related("member")
    for phase_state in phase_states:
        tasks.finalize(user_id=phase_state.member.user_id, game_id=game.id)


def _seeded_orchestration_rng():
    patcher = patch("agent.orchestration.random")
    mock_random = patcher.start()
    mock_random.Random = lambda: random.Random(7)
    return patcher


@pytest.mark.django_db
def test_all_dumbbot_game_plays_phases_without_inference(game_master_client, classical_variant):
    game = _create_game_master_game(game_master_client, classical_variant.id)
    dumbbots = list(UserProfile.objects.addable_to_game(game).filter(kind=UserKind.DUMBBOT)[:7])
    assert len(dumbbots) == 7
    _add_bots(game_master_client, game, dumbbots)

    assert game.status == GameStatus.ACTIVE
    assert game.current_phase.status == PhaseStatus.ACTIVE

    patcher = _seeded_orchestration_rng()
    try:
        for _ in range(3):
            phase = game.current_phase
            _finalize_all(game)

            pending = phase.phase_states.filter(has_possible_orders=True, orders_confirmed=False)
            assert not pending.exists()

            response = game_master_client.post(reverse("phase-resolve-all"))
            assert response.status_code == status.HTTP_200_OK
            assert response.data["resolved"] >= 1

            game.refresh_from_db()
            assert game.current_phase.id != phase.id
            assert game.current_phase.status == PhaseStatus.ACTIVE
    finally:
        patcher.stop()

    assert Inference.objects.count() == 0

    score = sum_of_squares(game.current_phase)
    assert set(score.kinds.values()) == {UserKind.DUMBBOT}
    assert score.total > 0
    assert all(count >= 0 for count in score.centers.values())
    assert score.cohorts == {UserKind.DUMBBOT: score.total}


@pytest.mark.django_db
def test_dumbbot_game_submits_orders_for_every_unit(game_master_client, classical_variant):
    game = _create_game_master_game(game_master_client, classical_variant.id)
    dumbbots = list(UserProfile.objects.addable_to_game(game).filter(kind=UserKind.DUMBBOT)[:7])
    _add_bots(game_master_client, game, dumbbots)

    patcher = _seeded_orchestration_rng()
    try:
        _finalize_all(game)
    finally:
        patcher.stop()

    for phase_state in game.current_phase.phase_states.filter(has_possible_orders=True):
        assert phase_state.orders.exists()
        assert all(order.complete for order in phase_state.orders.all())
