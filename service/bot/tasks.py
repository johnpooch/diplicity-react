import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from procrastinate.contrib.django import app
from rest_framework.test import APIClient

from common.constants import OrderType

logger = logging.getLogger(__name__)


def _option_to_selected(option):
    order_type = option["order_type"]["id"]
    selected = [option["source"]["id"], order_type]

    if order_type == OrderType.BUILD:
        selected.append(option["unit_type"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
        selected.append(option["target"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.SUPPORT, OrderType.CONVOY):
        selected.append(option["aux"]["id"])
        selected.append(option["target"]["id"])

    return selected


def _first_legal_selections(options):
    first_by_source = {}
    for option in options:
        source_id = option["source"]["id"]
        if source_id not in first_by_source:
            first_by_source[source_id] = _option_to_selected(option)
    return list(first_by_source.values())


def _authenticated_client(user_id):
    user = get_user_model().objects.get(id=user_id)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _submit_orders(client, game_id, label):
    options_response = client.get(reverse("order-options", args=[game_id]))
    if options_response.status_code != 200:
        logger.error(f"[{label}] options request failed: {options_response.status_code}")
        return

    create_url = reverse("order-create", args=[game_id])
    for selected in _first_legal_selections(options_response.data["orders"]):
        response = client.post(create_url, {"selected": selected}, format="json")
        if response.status_code not in (200, 201):
            logger.error(
                f"[{label}] create order failed ({response.status_code}) for {selected}"
            )


@app.task(name="bot.plan", retry=3)
def plan(user_id, game_id):
    label = f"bot.plan user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")
    client = _authenticated_client(user_id)
    _submit_orders(client, game_id, label)
    logger.info(f"[{label}] completed")


@app.task(name="bot.finalize", retry=3)
def finalize(user_id, game_id):
    label = f"bot.finalize user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")
    client = _authenticated_client(user_id)
    _submit_orders(client, game_id, label)

    game_response = client.get(reverse("game-retrieve", args=[game_id]))
    if game_response.status_code != 200:
        logger.error(f"[{label}] game retrieve failed: {game_response.status_code}")
        return

    if game_response.data.get("phase_confirmed"):
        logger.info(f"[{label}] orders already confirmed; skipping confirm")
        return

    confirm_response = client.put(reverse("game-confirm-phase", args=[game_id]))
    if confirm_response.status_code != 200:
        logger.error(f"[{label}] confirm failed: {confirm_response.status_code}")
        return

    logger.info(f"[{label}] completed")
