import pytest
from django.urls import reverse
from rest_framework import status

from common.constants import DeadlineMode, GameStatus, NationAssignment, PhaseStatus
from game.models import Game
from agent import tasks
from agent.fallback import first_legal_selections
from bot_profile.models import BotProfile


def _submit_first_legal_orders(client, game_id):
    options = client.get(reverse("order-options", args=[game_id])).data["orders"]
    create_url = reverse("order-create", args=[game_id])
    for selected in first_legal_selections(options):
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
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    game = Game.objects.get(id=response.data["id"])

    bot_user = BotProfile.objects.available_for_game(game).first().user
    add_response = client.post(
        reverse("game-add-bot", args=[game.id]), {"user_id": bot_user.id}, format="json"
    )
    assert add_response.status_code == status.HTTP_201_CREATED

    game.refresh_from_db()
    return game, bot_user


@pytest.fixture
def allowlisted_human(authenticated_client, primary_user, settings):
    settings.BOT_OPPONENT_ALLOWLIST = [primary_user.email.lower()]
    return authenticated_client


@pytest.mark.django_db
def test_bot_game_starts_on_creation_and_plays_phase(
    allowlisted_human, italy_vs_germany_variant
):
    human_client = allowlisted_human
    game, bot_user = _create_bot_game(human_client, italy_vs_germany_variant.id)

    assert game.status == GameStatus.ACTIVE
    first_phase = game.current_phase
    assert first_phase.status == PhaseStatus.ACTIVE

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
def test_bot_plans_when_variant_has_no_adjacencies(allowlisted_human, italy_vs_germany_variant):
    from province.models import Province

    Province.objects.filter(variant=italy_vs_germany_variant).update(adjacencies=[])
    human_client = allowlisted_human
    game, bot_user = _create_bot_game(human_client, italy_vs_germany_variant.id)

    tasks.plan(user_id=bot_user.id, game_id=game.id)

    bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)
    assert bot_phase_state.orders.exists()


@pytest.mark.django_db
def test_bot_can_play_the_next_phase(allowlisted_human, italy_vs_germany_variant):
    human_client = allowlisted_human
    game, bot_user = _create_bot_game(human_client, italy_vs_germany_variant.id)
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
