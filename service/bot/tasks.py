import itertools
import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from procrastinate.contrib.django import app
from rest_framework.test import APIClient

from bot.utils import first_legal_selections

logger = logging.getLogger(__name__)


def _get_max_orders(client, game_id, label):
    phase_states_response = client.get(reverse("phase-state-list", args=[game_id]))
    if phase_states_response.status_code != 200:
        logger.warning(f"[{label}] phase-state-list request failed: {phase_states_response.status_code}")
        return None
    phase_states = phase_states_response.data
    if not phase_states:
        return None
    return phase_states[0].get("max_orders")


@app.task(name="bot.plan", retry=3)
def plan(user_id, game_id):
    label = f"bot.plan user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    user = get_user_model().objects.get(id=user_id)
    client = APIClient()
    client.force_authenticate(user=user)

    options_response = client.get(reverse("order-options", args=[game_id]))
    if options_response.status_code != 200:
        logger.error(f"[{label}] options request failed: {options_response.status_code}")
        return

    max_orders = _get_max_orders(client, game_id, label)
    selections = first_legal_selections(options_response.data["orders"])
    if max_orders is not None:
        selections = itertools.islice(selections, max_orders)

    create_url = reverse("order-create", args=[game_id])
    for selected in selections:
        response = client.post(create_url, {"selected": selected}, format="json")
        if response.status_code not in (200, 201):
            logger.info(
                f"[{label}] order {selected} rejected ({response.status_code}); stopping"
            )
            break

    logger.info(f"[{label}] completed")


@app.task(name="bot.finalize", retry=3)
def finalize(user_id, game_id):
    label = f"bot.finalize user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    user = get_user_model().objects.get(id=user_id)
    client = APIClient()
    client.force_authenticate(user=user)

    game_response = client.get(reverse("game-retrieve", args=[game_id]))
    if game_response.status_code != 200:
        logger.error(f"[{label}] game retrieve failed: {game_response.status_code}")
        return
    if game_response.data.get("phase_confirmed"):
        logger.info(f"[{label}] orders already confirmed; skipping")
        return

    options_response = client.get(reverse("order-options", args=[game_id]))
    if options_response.status_code != 200:
        logger.error(f"[{label}] options request failed: {options_response.status_code}")
        return

    max_orders = _get_max_orders(client, game_id, label)
    selections = first_legal_selections(options_response.data["orders"])
    if max_orders is not None:
        selections = itertools.islice(selections, max_orders)

    create_url = reverse("order-create", args=[game_id])
    for selected in selections:
        response = client.post(create_url, {"selected": selected}, format="json")
        if response.status_code not in (200, 201):
            logger.info(
                f"[{label}] order {selected} rejected ({response.status_code}); stopping"
            )
            break

    confirm_response = client.put(reverse("game-confirm-phase", args=[game_id]))
    if confirm_response.status_code != 200:
        logger.error(f"[{label}] confirm failed: {confirm_response.status_code}")
        return

    logger.info(f"[{label}] completed")
