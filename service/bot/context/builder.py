import logging

from common.constants import PhaseType

from bot.context.map import build_graph, nearest_enemy_units, nearest_uncontrolled_supply_centers, pass_type_for_unit
from bot.context.orders import group_options_by_source, order_option_label
from bot.types import ChannelDict, ChatMessageDict, ContextData, UnitDict

logger = logging.getLogger(__name__)


def _sender_label(message: ChatMessageDict) -> str:
    nation = (message["sender"].get("nation") or {}).get("name")
    return nation or "user"


def _unit_label(unit: UnitDict) -> str:
    return f"{unit['type'][0].upper()} {unit['province']['id']}"


class ContextBuilder:
    def __init__(self, data: ContextData):
        self._data = data
        self._shared_sections: list[str] = []
        self._private_sections: list[str] = []

    def with_game_state(self) -> "ContextBuilder":
        phase = self._data["phase"]
        if not phase:
            return self

        lines = [f"Current phase: {phase['name']}"]

        units_by_nation: dict[str, list[str]] = {}
        for unit in sorted(phase.get("units", []), key=lambda u: u["province"]["id"]):
            label = _unit_label(unit)
            if unit.get("dislodged"):
                label += " (dislodged)"
            units_by_nation.setdefault(unit["nation"]["name"], []).append(label)

        lines.append("Units:")
        for nation in sorted(units_by_nation):
            labels = units_by_nation[nation]
            lines.append(f"  {nation}: {len(labels)} ({', '.join(labels)})")

        centers_by_nation: dict[str, list[str]] = {}
        for center in phase.get("supply_centers", []):
            centers_by_nation.setdefault(center["nation"]["name"], []).append(
                center["province"]["id"]
            )

        lines.append("Supply centers:")
        for nation in sorted(centers_by_nation):
            provinces = sorted(centers_by_nation[nation])
            lines.append(f"  {nation}: {len(provinces)} ({', '.join(provinces)})")

        if phase.get("type") == PhaseType.RETREAT:
            lines.append("")
            lines.append(self._dislodged_units_line(phase))
        elif phase.get("type") == PhaseType.ADJUSTMENT:
            lines.append("")
            lines.extend(self._adjustments_lines(units_by_nation, centers_by_nation))

        self._shared_sections.append("\n".join(lines))
        return self

    def _dislodged_units_line(self, phase) -> str:
        dislodged = sorted(
            (unit for unit in phase.get("units", []) if unit.get("dislodged")),
            key=lambda u: u["province"]["id"],
        )
        if not dislodged:
            return "Dislodged units: none"
        entries = [f"{_unit_label(unit)} ({unit['nation']['name']})" for unit in dislodged]
        return f"Dislodged units: {', '.join(entries)}"

    def _adjustments_lines(self, units_by_nation, centers_by_nation) -> list[str]:
        lines = ["Adjustments:"]
        for nation in sorted(set(units_by_nation) | set(centers_by_nation)):
            delta = len(centers_by_nation.get(nation, [])) - len(units_by_nation.get(nation, []))
            if delta > 0:
                summary = f"{delta} build{'s' if delta != 1 else ''} available"
            elif delta < 0:
                summary = f"{-delta} disband{'s' if delta != -1 else ''} required"
            else:
                summary = "no change"
            lines.append(f"  {nation}: {summary}")
        return lines

    def with_tactical_annotations(self) -> "ContextBuilder":
        provinces = self._data.get("variant", {}).get("provinces", [])
        units = self._data["phase"].get("units", []) if self._data["phase"] else []
        if not provinces or not units:
            return self

        graph = build_graph(provinces)
        supply_center_ids = {p["id"] for p in provinces if p.get("supply_center") and not p.get("parent_id")}
        owners = {
            graph["canonical"].get(c["province"]["id"], c["province"]["id"]): c["nation"]["name"]
            for c in self._data["phase"].get("supply_centers", [])
        }
        occupants: dict[str, list[UnitDict]] = {}
        for unit in units:
            province_id = graph["canonical"].get(unit["province"]["id"], unit["province"]["id"])
            occupants.setdefault(province_id, []).append(unit)

        lines = ["Tactical annotations:"]
        ordered_units = sorted(
            units,
            key=lambda u: (u["province"]["id"], bool(u.get("dislodged")), u["nation"]["name"]),
        )
        for unit in ordered_units:
            header = f"Unit {_unit_label(unit)} ({unit['nation']['name']}"
            if unit.get("dislodged"):
                header += ", dislodged"
            lines.append(f"{header}):")
            lines.append(f"  Adjacent: {self._adjacent_entries(unit, graph, supply_center_ids, owners, occupants)}")
            lines.append(f"  Nearest enemy units: {self._nearest_enemy_entries(unit, graph)}")
            lines.append(
                f"  Nearest uncontrolled supply centers: {self._nearest_supply_center_entries(unit, graph)}"
            )
        self._shared_sections.append("\n".join(lines))
        return self

    def _adjacent_entries(self, unit, graph, supply_center_ids, owners, occupants) -> str:
        province_id = graph["canonical"].get(unit["province"]["id"], unit["province"]["id"])
        neighbours = graph["edges"].get(province_id, {}).get(pass_type_for_unit(unit["type"]), [])
        if not neighbours:
            return "none"
        entries = []
        for neighbour in neighbours:
            if neighbour in supply_center_ids:
                sc_part = f"SC: {owners.get(neighbour, 'unowned')}"
            else:
                sc_part = "no SC"
            entries.append(f"{neighbour} ({sc_part}, {self._occupancy(occupants.get(neighbour, []))})")
        return ", ".join(entries)

    def _occupancy(self, units: list[UnitDict]) -> str:
        standing = [unit for unit in units if not unit.get("dislodged")]
        if standing:
            unit = standing[0]
            return f"occupied {_unit_label(unit)} {unit['nation']['name']}"
        if units:
            unit = units[0]
            return f"occupied {_unit_label(unit)} {unit['nation']['name']} (dislodged)"
        return "empty"

    def _nearest_enemy_entries(self, unit, graph) -> str:
        nearest = nearest_enemy_units(self._data, graph, unit)
        if not nearest:
            return "none"
        return ", ".join(
            f"{_unit_label(enemy)} ({enemy['nation']['name']}, dist {distance})"
            for enemy, distance in nearest
        )

    def _nearest_supply_center_entries(self, unit, graph) -> str:
        nearest = nearest_uncontrolled_supply_centers(self._data, graph, unit)
        if not nearest:
            return "none"
        return ", ".join(
            f"{province_id} ({owner or 'unowned'}, dist {distance})"
            for province_id, owner, distance in nearest
        )

    def with_identity(self) -> "ContextBuilder":
        phase_states = self._data["phase_states"]
        nation = phase_states[0].get("member", {}).get("nation") if phase_states else None
        if nation:
            self._private_sections.append(f"You are playing {nation}.")
        return self

    def with_orders(self) -> "ContextBuilder":
        lines = ["Legal orders:"]
        options_by_source = group_options_by_source(self._data["orders"])
        for source_id in sorted(options_by_source):
            lines.append(f"Unit {source_id}:")
            for index, option in enumerate(options_by_source[source_id]):
                lines.append(f"  {index}. {order_option_label(option)}")
        self._private_sections.append("\n".join(lines))
        return self

    def with_phase_state(self) -> "ContextBuilder":
        phase_states = self._data["phase_states"]
        if phase_states:
            max_orders = phase_states[0].get("max_orders")
            if max_orders is not None:
                self._private_sections.append(f"Orders to submit this phase: {max_orders}")
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
