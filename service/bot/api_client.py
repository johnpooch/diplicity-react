import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from bot.utils import bot_request_host

logger = logging.getLogger(__name__)


class ApiClientError(Exception):
    pass


class ApiClient:
    def __init__(self, user):
        self._client = APIClient(SERVER_NAME=bot_request_host())
        self._client.force_authenticate(user=user)

    @classmethod
    def for_user(cls, user_id):
        user = get_user_model().objects.get(id=user_id)
        return cls(user)

    def get_order_options(self, game_id):
        response = self._client.get(reverse("order-options", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(f"options request failed: {response.status_code}")
        orders = response.data["orders"]
        logger.info(f"[bot.api] fetched {len(orders)} order option(s)")
        return orders

    def get_phase_states(self, game_id):
        response = self._client.get(reverse("phase-state-list", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(f"phase states request failed: {response.status_code}")
        return list(response.data)

    def get_game(self, game_id):
        response = self._client.get(reverse("game-retrieve", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(f"game retrieve failed: {response.status_code}")
        return response.data

    def get_channels(self, game_id):
        response = self._client.get(reverse("channel-list", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(f"channel list request failed: {response.status_code}")
        return list(response.data)

    def submit_orders(self, game_id, selections):
        create_url = reverse("order-create", args=[game_id])
        for selected in selections:
            response = self._client.post(create_url, {"selected": selected}, format="json")
            if response.status_code not in (200, 201):
                logger.error(f"[bot.api] create order failed ({response.status_code}) for {selected}")
            else:
                logger.info(f"[bot.api] created order {selected}")

    def confirm_phase(self, game_id):
        response = self._client.put(reverse("game-confirm-phase", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(f"confirm failed: {response.status_code}")
        logger.info("[bot.api] confirmed phase")

    def post_message(self, game_id, channel_id, body):
        create_url = reverse("channel-message-create", args=[game_id, channel_id])
        response = self._client.post(create_url, {"body": body}, format="json")
        if response.status_code not in (200, 201):
            raise ApiClientError(f"post reply failed: {response.status_code}")
        logger.info("[bot.api] posted reply")
