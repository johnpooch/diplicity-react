from harness.exceptions import ContextError
from harness.types import Channel, Context
from harness.utils import current_nation


def _channel(context: Context, channel_id: int) -> Channel:
    for channel in context["channels"]:
        if channel["id"] == channel_id:
            return channel
    raise ContextError(f"channel {channel_id} not in context")


def user_prompt(context: Context, channel_id: int) -> str:
    nation = current_nation(context)
    channel = _channel(context, channel_id)
    phase = context["phase"]

    lines = [
        f"You are playing as {nation}.",
        f"The current phase is {phase['season']} {phase['year']}, {phase['type']}.",
    ]

    units_by_nation: dict[str, list[str]] = {}
    for unit in context["units"]:
        label = f"{unit['type'][0].upper()} {unit['province']}"
        if unit["dislodged"]:
            label += " (dislodged)"
        units_by_nation.setdefault(unit["nation"], []).append(label)
    if units_by_nation:
        lines.append("")
        lines.append("Units:")
        for unit_nation in sorted(units_by_nation):
            labels = units_by_nation[unit_nation]
            lines.append(f"  {unit_nation}: {len(labels)} ({', '.join(labels)})")

    centers_by_nation: dict[str, list[str]] = {}
    for center in context["supply_centers"]:
        if center["nation"]:
            centers_by_nation.setdefault(center["nation"], []).append(center["province"])
    if centers_by_nation:
        lines.append("")
        lines.append("Supply centers:")
        for center_nation in sorted(centers_by_nation):
            provinces = sorted(centers_by_nation[center_nation])
            lines.append(f"  {center_nation}: {len(provinces)} ({', '.join(provinces)})")

    privacy = "private" if channel["private"] else "public"
    lines.append("")
    lines.append(f"Channel: {channel['name']} ({privacy})")
    for message in channel["messages"]:
        lines.append(f"{message['sender']}: {message['body']}")

    return "\n".join(lines)
