import logging

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from bot.dto import ChatMessage, OrderOptionCollection
from bot.utils import bot_request_host

logger = logging.getLogger(__name__)


class BotApiError(Exception):
    pass


class BotApiClient:
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
            raise BotApiError(f"options request failed: {response.status_code}")
        orders = response.data["orders"]
        logger.info(f"[bot.api] fetched {len(orders)} order option(s)")
        return OrderOptionCollection.from_api(orders)

    def get_max_orders(self, game_id):
        response = self._client.get(reverse("phase-state-list", args=[game_id]))
        if response.status_code != 200:
            raise BotApiError(f"phase states request failed: {response.status_code}")
        if not response.data:
            return None
        return response.data[0]["max_orders"]

    def submit_orders(self, game_id, selections):
        create_url = reverse("order-create", args=[game_id])
        for selected in selections:
            response = self._client.post(create_url, {"selected": selected}, format="json")
            if response.status_code not in (200, 201):
                logger.error(f"[bot.api] create order failed ({response.status_code}) for {selected}")
            else:
                logger.info(f"[bot.api] created order {selected}")

    def is_phase_confirmed(self, game_id):
        response = self._client.get(reverse("game-retrieve", args=[game_id]))
        if response.status_code != 200:
            raise BotApiError(f"game retrieve failed: {response.status_code}")
        return bool(response.data.get("phase_confirmed"))

    def confirm_phase(self, game_id):
        response = self._client.put(reverse("game-confirm-phase", args=[game_id]))
        if response.status_code != 200:
            raise BotApiError(f"confirm failed: {response.status_code}")
        logger.info("[bot.api] confirmed phase")

    def get_channel_messages(self, game_id, channel_id):
        response = self._client.get(reverse("channel-list", args=[game_id]))
        if response.status_code != 200:
            raise BotApiError(f"channel list request failed: {response.status_code}")
        channel = next((c for c in response.data if c["id"] == channel_id), None)
        if channel is None:
            raise BotApiError(f"channel {channel_id} not found")
        return ChatMessage.list_from_api(channel["messages"])

    def post_message(self, game_id, channel_id, body):
        create_url = reverse("channel-message-create", args=[game_id, channel_id])
        response = self._client.post(create_url, {"body": body}, format="json")
        if response.status_code not in (200, 201):
            raise BotApiError(f"post reply failed: {response.status_code}")
        logger.info("[bot.api] posted reply")
