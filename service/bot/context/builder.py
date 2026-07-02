import logging

from bot.context.orders import group_options_by_source, order_option_label
from bot.types import ChannelDict, ChatMessageDict, ContextData

logger = logging.getLogger(__name__)


def _sender_label(message: ChatMessageDict) -> str:
    nation = (message["sender"].get("nation") or {}).get("name")
    return nation or "user"


class ContextBuilder:
    def __init__(self, data: ContextData):
        self._data = data
        self._shared_sections: list[str] = []
        self._private_sections: list[str] = []

    def _self_nation(self) -> str | None:
        for member in self._data["game"].get("members", []):
            if member.get("is_current_user"):
                return member.get("nation")
        return None

    def with_game_state(self) -> "ContextBuilder":
        phase = self._data["phase"]
        if not phase:
            return self

        lines = [f"Current phase: {phase['name']}"]

        self_nation = self._self_nation()
        if self_nation:
            lines.append(f"You are playing {self_nation}.")

        units_by_nation: dict[str, list[str]] = {}
        for unit in phase.get("units", []):
            label = f"{unit['type'][0].upper()} {unit['province']['id']}"
            if unit.get("dislodged"):
                label += " (dislodged)"
            units_by_nation.setdefault(unit["nation"]["name"], []).append(label)

        lines.append("Units:")
        for nation in sorted(units_by_nation):
            lines.append(f"  {nation}: {', '.join(units_by_nation[nation])}")

        centers_by_nation: dict[str, list[str]] = {}
        for center in phase.get("supply_centers", []):
            centers_by_nation.setdefault(center["nation"]["name"], []).append(
                center["province"]["id"]
            )

        lines.append("Supply centers:")
        for nation in sorted(centers_by_nation):
            provinces = sorted(centers_by_nation[nation])
            lines.append(f"  {nation}: {len(provinces)} ({', '.join(provinces)})")

        self._shared_sections.append("\n".join(lines))
        return self

    def with_orders(self) -> "ContextBuilder":
        lines = ["Legal orders:"]
        for source_id, source_options in group_options_by_source(self._data["orders"]).items():
            lines.append(f"Unit {source_id}:")
            for index, option in enumerate(source_options):
                lines.append(f"  {index}. {order_option_label(option)}")
        self._shared_sections.append("\n".join(lines))
        return self

    def with_phase_state(self) -> "ContextBuilder":
        phase_states = self._data["phase_states"]
        if phase_states:
            max_orders = phase_states[0].get("max_orders")
            if max_orders is not None:
                self._shared_sections.append(f"Orders to submit this phase: {max_orders}")
        return self

    def with_conversations(self) -> "ContextBuilder":
        sections = [self._format_channel(channel) for channel in self._data["channels"]]
        if sections:
            self._private_sections.append("\n\n".join(sections))
        return self

    def with_messages(self, channel_id) -> "ContextBuilder":
        channel = next(
            (c for c in self._data["channels"] if c["id"] == channel_id), None
        )
        if channel is None:
            logger.info(f"[bot.context] channel {channel_id} not in fetched data; skipping")
            return self
        self._private_sections.append(self._format_channel(channel))
        return self

    def _format_channel(self, channel: ChannelDict) -> str:
        privacy = "private" if channel.get("private") else "public"
        lines = [f"Channel: {channel.get('name') or channel['id']} ({privacy})"]
        for message in channel["messages"]:
            lines.append(f"{_sender_label(message)}: {message['body']}")
        return "\n".join(lines)

    def build_shared(self) -> str:
        return "\n\n".join(self._shared_sections)

    def build_private(self) -> str:
        return "\n\n".join(self._private_sections)
