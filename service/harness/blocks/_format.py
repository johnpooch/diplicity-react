from harness.types import ChannelDict, ChatMessageDict, UnitDict


def unit_label(unit: UnitDict) -> str:
    return f"{unit['type'][0].upper()} {unit['province']['id']}"


def sender_label(message: ChatMessageDict) -> str:
    nation = (message["sender"].get("nation") or {}).get("name")
    return nation or "user"


def format_channel(channel: ChannelDict) -> str:
    privacy = "private" if channel.get("private") else "public"
    lines = [f"Channel: {channel.get('name') or channel['id']} ({privacy})"]
    for message in channel["messages"]:
        lines.append(f"{sender_label(message)}: {message['body']}")
    return "\n".join(lines)
