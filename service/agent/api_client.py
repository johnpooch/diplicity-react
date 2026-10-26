import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from common.constants import ChannelMessagePagination

logger = logging.getLogger(__name__)


class ApiClientError(Exception):
    pass


def bot_request_host():
    for host in settings.ALLOWED_HOSTS:
        if host and host != "*":
            return host.lstrip(".")
    return "testserver"


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
        logger.info(f"[agent.api] fetched {len(orders)} order option(s)")
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

    def get_variant(self, variant_id):
        response = self._client.get(reverse("variant-detail", args=[variant_id]))
        if response.status_code != 200:
            raise ApiClientError(f"variant retrieve failed: {response.status_code}")
        return response.data

    def get_phase(self, game_id, phase_id):
        response = self._client.get(reverse("phase-retrieve", args=[game_id, phase_id]))
        if response.status_code != 200:
            raise ApiClientError(f"phase retrieve failed: {response.status_code}")
        return response.data

    def get_channels(self, game_id):
        response = self._client.get(reverse("channel-preview-list", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(
                f"channel preview request failed: {response.status_code}"
            )
        return [self.get_channel(game_id, preview["id"]) for preview in response.data]

    def get_channel(self, game_id, channel_id):
        response = self._client.get(
            reverse("channel-update", args=[game_id, channel_id])
        )
        if response.status_code != 200:
            raise ApiClientError(f"channel retrieve failed: {response.status_code}")
        channel = response.data
        return {
            "id": channel["id"],
            "name": channel["name"],
            "title": channel["title"],
            "private": channel["private"],
            "messages": self.get_channel_messages(game_id, channel_id),
            "events": channel["events"],
            "unread_message_count": channel["unread_message_count"],
            "muted": channel["muted"],
            "can_rename": channel["can_rename"],
            "can_mute": channel["can_mute"],
        }

    def get_channel_messages(self, game_id, channel_id):
        url = reverse("channel-message-list", args=[game_id, channel_id])
        params = {"page_size": ChannelMessagePagination.MAX_PAGE_SIZE}
        pages = []
        while True:
            response = self._client.get(url, params)
            if response.status_code != 200:
                raise ApiClientError(
                    f"channel message request failed: {response.status_code}"
                )
            results = response.data["results"]
            pages.append(results)
            if not response.data["has_older"]:
                break
            params = {**params, "before": min(message["id"] for message in results)}
        return [message for page in reversed(pages) for message in page]

    def submit_orders(self, game_id, selections):
        create_url = reverse("order-create", args=[game_id])
        for selected in selections:
            response = self._client.post(
                create_url, {"selected": selected}, format="json"
            )
            if response.status_code not in (200, 201):
                logger.error(
                    f"[agent.api] create order failed ({response.status_code}) for {selected}"
                )
            else:
                logger.info(f"[agent.api] created order {selected}")

    def confirm_phase(self, game_id):
        response = self._client.put(reverse("game-confirm-phase", args=[game_id]))
        if response.status_code != 200:
            raise ApiClientError(f"confirm failed: {response.status_code}")
        logger.info("[agent.api] confirmed phase")

    def post_message(self, game_id, channel_id, body):
        create_url = reverse("channel-message-create", args=[game_id, channel_id])
        response = self._client.post(create_url, {"body": body}, format="json")
        if response.status_code not in (200, 201):
            raise ApiClientError(
                f"post reply failed: {response.status_code}: {response.data}"
            )
        logger.info("[agent.api] posted reply")
