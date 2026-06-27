from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from adjudication import service as adjudication_service
from common.constants import DeadlineMode, MovementPhaseDuration, NationAssignment, PhaseStatus
from game.models import Game
from bot import tasks
from bot.utils import get_bot_user


@pytest.fixture
def bot_game(db, primary_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany):
    game = Game.objects.create_from_template(
        italy_vs_germany_variant,
        name="Bot Integration Game",
        nation_assignment=NationAssignment.ORDERED,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        created_by=primary_user,
    )
    game.members.create(user=primary_user)
    game.members.create(user=get_bot_user())
    with patch.object(
        adjudication_service, "start", return_value=adjudication_data_italy_vs_germany
    ):
        game.start()
    return game


@pytest.mark.django_db
def test_bot_plays_phase_and_game_advances(bot_game):
    game = bot_game
    bot_user = get_bot_user()
    first_phase = game.current_phase

    human_client = APIClient()
    human_client.force_authenticate(user=game.created_by)

    tasks.plan(user_id=bot_user.id, game_id=game.id)

    bot_phase_state = first_phase.phase_states.get(member__user=bot_user)
    assert bot_phase_state.orders.exists()
    assert bot_phase_state.orders_confirmed is False

    tasks._submit_orders(human_client, game.id, "human")
    confirm_response = human_client.put(reverse("game-confirm-phase", args=[game.id]))
    assert confirm_response.status_code == status.HTTP_200_OK

    tasks.finalize(user_id=bot_user.id, game_id=game.id)
    bot_phase_state.refresh_from_db()
    assert bot_phase_state.orders_confirmed is True

    resolve_response = human_client.post(reverse("phase-resolve-all"))
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    game.refresh_from_db()
    second_phase = game.current_phase
    assert second_phase.id != first_phase.id
    assert second_phase.status == PhaseStatus.ACTIVE


@pytest.mark.django_db
def test_bot_can_play_the_next_phase(bot_game):
    game = bot_game
    bot_user = get_bot_user()
    first_phase = game.current_phase

    human_client = APIClient()
    human_client.force_authenticate(user=game.created_by)

    tasks.plan(user_id=bot_user.id, game_id=game.id)
    tasks._submit_orders(human_client, game.id, "human")
    human_client.put(reverse("game-confirm-phase", args=[game.id]))
    tasks.finalize(user_id=bot_user.id, game_id=game.id)
    human_client.post(reverse("phase-resolve-all"))

    game.refresh_from_db()
    second_phase = game.current_phase
    assert second_phase.id != first_phase.id

    tasks.plan(user_id=bot_user.id, game_id=game.id)

    bot_phase_state = second_phase.phase_states.filter(member__user=bot_user).first()
    if bot_phase_state is not None and bot_phase_state.has_possible_orders:
        assert bot_phase_state.orders.exists()
