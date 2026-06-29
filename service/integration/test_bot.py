import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from common.constants import DeadlineMode, GameStatus, NationAssignment, PhaseStatus
from game.models import Game
from bot import tasks
from bot.dto import OrderOptionCollection
from bot.utils import get_bot_user


def _submit_first_legal_orders(client, game_id):
    options = client.get(reverse("order-options", args=[game_id])).data["orders"]
    create_url = reverse("order-create", args=[game_id])
    for selected in OrderOptionCollection.from_api(options).first_legal_selections():
        client.post(create_url, {"selected": selected}, format="json")


def _create_bot_game(client, variant_id):
    response = client.post(
        reverse("game-create"),
        {
            "name": "Bot Integration Game",
            "variant_id": variant_id,
            "nation_assignment": NationAssignment.ORDERED,
            "private": False,
            "deadline_mode": DeadlineMode.DURATION,
            "include_bot_opponent": True,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return Game.objects.get(id=response.data["id"])


@pytest.fixture
def allowlisted_human(authenticated_client, primary_user, settings):
    settings.BOT_OPPONENT_ALLOWLIST = [primary_user.email.lower()]
    return authenticated_client


@pytest.mark.django_db
def test_bot_game_starts_on_creation_and_plays_phase(
    allowlisted_human, italy_vs_germany_variant
):
    human_client = allowlisted_human
    game = _create_bot_game(human_client, italy_vs_germany_variant.id)

    assert game.status == GameStatus.ACTIVE
    first_phase = game.current_phase
    assert first_phase.status == PhaseStatus.ACTIVE

    bot_user = get_bot_user()
    tasks.plan(user_id=bot_user.id, game_id=game.id)

    bot_phase_state = first_phase.phase_states.get(member__user=bot_user)
    assert bot_phase_state.orders.exists()
    assert bot_phase_state.orders_confirmed is False

    _submit_first_legal_orders(human_client, game.id)
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
def test_bot_can_play_the_next_phase(allowlisted_human, italy_vs_germany_variant):
    human_client = allowlisted_human
    game = _create_bot_game(human_client, italy_vs_germany_variant.id)
    bot_user = get_bot_user()
    first_phase = game.current_phase

    tasks.plan(user_id=bot_user.id, game_id=game.id)
    _submit_first_legal_orders(human_client, game.id)
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
