import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from procrastinate.contrib.django import app
from rest_framework.test import APIClient

from bot.llm import select_orders
from bot.utils import bot_request_host

logger = logging.getLogger(__name__)


@app.task(name="bot.plan", retry=3)
def plan(user_id, game_id):
    label = f"bot.plan user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    user = get_user_model().objects.get(id=user_id)
    client = APIClient(SERVER_NAME=bot_request_host())
    client.force_authenticate(user=user)

    options_response = client.get(reverse("order-options", args=[game_id]))
    if options_response.status_code != 200:
        logger.error(f"[{label}] options request failed: {options_response.status_code}")
        return
    logger.info(f"[{label}] fetched {len(options_response.data['orders'])} order option(s)")
    selections = select_orders(options_response.data["orders"])

    phase_states_response = client.get(reverse("phase-state-list", args=[game_id]))
    if phase_states_response.status_code != 200:
        logger.error(f"[{label}] phase states request failed: {phase_states_response.status_code}")
        return
    max_orders = phase_states_response.data[0]["max_orders"] if phase_states_response.data else None
    if max_orders is not None and len(selections) > max_orders:
        logger.info(f"[{label}] capping {len(selections)} selection(s) to max_orders={max_orders}")
        selections = selections[:max_orders]

    create_url = reverse("order-create", args=[game_id])
    for selected in selections:
        response = client.post(create_url, {"selected": selected}, format="json")
        if response.status_code not in (200, 201):
            logger.error(f"[{label}] create order failed ({response.status_code}) for {selected}")
        else:
            logger.info(f"[{label}] created order {selected}")

    logger.info(f"[{label}] completed")


@app.task(name="bot.finalize", retry=3)
def finalize(user_id, game_id):
    label = f"bot.finalize user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    user = get_user_model().objects.get(id=user_id)
    client = APIClient(SERVER_NAME=bot_request_host())
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
    logger.info(f"[{label}] fetched {len(options_response.data['orders'])} order option(s)")
    selections = select_orders(options_response.data["orders"])

    phase_states_response = client.get(reverse("phase-state-list", args=[game_id]))
    if phase_states_response.status_code != 200:
        logger.error(f"[{label}] phase states request failed: {phase_states_response.status_code}")
        return
    max_orders = phase_states_response.data[0]["max_orders"] if phase_states_response.data else None
    if max_orders is not None and len(selections) > max_orders:
        logger.info(f"[{label}] capping {len(selections)} selection(s) to max_orders={max_orders}")
        selections = selections[:max_orders]

    create_url = reverse("order-create", args=[game_id])
    for selected in selections:
        response = client.post(create_url, {"selected": selected}, format="json")
        if response.status_code not in (200, 201):
            logger.error(f"[{label}] create order failed ({response.status_code}) for {selected}")
        else:
            logger.info(f"[{label}] created order {selected}")

    confirm_response = client.put(reverse("game-confirm-phase", args=[game_id]))
    if confirm_response.status_code != 200:
        logger.error(f"[{label}] confirm failed: {confirm_response.status_code}")
        return
    logger.info(f"[{label}] confirmed phase")

    logger.info(f"[{label}] completed")
