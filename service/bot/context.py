from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from bot.core.types import BotContext
from common.constants import ChannelMessagePagination

PASS_TO_ALLOWS = {
    "army": ["army"],
    "fleet": ["fleet"],
    "both": ["army", "fleet"],
}


class ContextError(Exception):
    pass


class BotContextBuilder:
    def __init__(self, member):
        self.member = member
        self.client = APIClient(SERVER_NAME=self.host())
        self.client.force_authenticate(user=member.user)

    def host(self):
        for host in settings.ALLOWED_HOSTS:
            if host and host != "*":
                return host.lstrip(".")
        return "testserver"

    def get(self, name, *args, params=None):
        response = self.client.get(reverse(name, args=args), params)
        if response.status_code != 200:
            raise ContextError(name, response.status_code)
        return response.data

    def build(self) -> BotContext:
        game_id = self.member.game_id
        game = self.get("game-retrieve", game_id)
        phase = self.get("phase-retrieve", game_id, game["current_phase_id"])
        variant = self.get("variant-detail", game["variant_id"])
        phase_states = self.get("phase-state-list", game_id)
        options = self.get("order-options", game_id)["orders"]
        previews = self.get("channel-preview-list", game_id)
        return {
            "member_id": self.member.id,
            "members": [
                {
                    "name": member["name"],
                    "nation": member["nation"],
                    "is_current_user": member["is_current_user"],
                }
                for member in game["members"]
                if member["nation"]
            ],
            "phase": {
                "season": phase["season"],
                "year": phase["year"],
                "type": phase["type"],
            },
            "max_orders": next(
                (
                    phase_state["max_orders"]
                    for phase_state in phase_states
                    if phase_state["member"]["is_current_user"]
                ),
                None,
            ),
            "provinces": [
                {
                    "id": province["id"],
                    "name": province["name"],
                    "type": province["type"],
                    "supply_center": province["supply_center"],
                    "parent_id": province["parent_id"],
                    "adjacencies": [
                        {
                            "to": adjacency["to"],
                            "allows": PASS_TO_ALLOWS[adjacency["pass"]],
                        }
                        for adjacency in province["adjacencies"]
                    ],
                }
                for province in variant["provinces"]
            ],
            "units": [
                {
                    "type": unit["type"],
                    "nation": unit["nation"]["name"],
                    "province": unit["province"]["id"],
                    "dislodged": unit["dislodged"],
                }
                for unit in phase["units"]
            ],
            "supply_centers": self.supply_centers(variant, phase),
            "order_options": [
                {
                    "source": option["source"]["id"],
                    "order_type": option["order_type"]["id"],
                    "target": self.field(option["target"]),
                    "aux": self.field(option["aux"]),
                    "unit_type": self.field(option["unit_type"]),
                    "named_coast": self.field(option["named_coast"]),
                }
                for option in options
                if option["source"] is not None and option["order_type"] is not None
            ],
            "channels": [
                {
                    "id": preview["id"],
                    "messages": [
                        {"sender_id": message["sender"]["id"], "body": message["body"]}
                        for message in self.messages(game_id, preview["id"])
                    ],
                }
                for preview in previews
            ],
            "nations": [nation["name"] for nation in variant["nations"]],
        }

    def field(self, value):
        return None if value is None else value["id"]

    def supply_centers(self, variant, phase):
        owners = {
            center["province"]["id"]: center["nation"]["name"]
            for center in phase["supply_centers"]
        }
        return [
            {"nation": owners.get(province["id"]), "province": province["id"]}
            for province in variant["provinces"]
            if province["supply_center"]
        ]

    def messages(self, game_id, channel_id):
        params = {"page_size": ChannelMessagePagination.MAX_PAGE_SIZE}
        pages = []
        while True:
            page = self.get("channel-message-list", game_id, channel_id, params=params)
            pages.append(page["results"])
            if not page["has_older"]:
                break
            params = {
                **params,
                "before": min(message["id"] for message in page["results"]),
            }
        return [message for page in reversed(pages) for message in page]
