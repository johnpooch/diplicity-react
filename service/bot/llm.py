import logging

from anthropic import Anthropic
from django.conf import settings

from bot.utils import first_legal_selections, option_to_selected

logger = logging.getLogger(__name__)

TOOL_NAME = "submit_order_choices"

TOOL = {
    "name": TOOL_NAME,
    "description": "Submit the chosen order index for each unit.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "choices": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_id": {"type": "string"},
                        "option_index": {"type": "integer"},
                    },
                    "required": ["source_id", "option_index"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["choices"],
        "additionalProperties": False,
    },
}


def group_by_source(options):
    grouped = {}
    for option in options:
        grouped.setdefault(option["source"]["id"], []).append(option)
    return grouped


def option_label(option):
    parts = [option["source"]["id"], option["order_type"]["id"]]
    for key in ("aux", "target", "unit_type", "named_coast"):
        value = option.get(key)
        if value:
            parts.append(value["id"])
    return " ".join(parts)


def build_prompt(grouped):
    lines = []
    for source_id, source_options in grouped.items():
        lines.append(f"Unit {source_id}:")
        for index, option in enumerate(source_options):
            lines.append(f"  {index}. {option_label(option)}")
    return (
        "You are playing a game of Diplomacy. For each unit below, choose one order "
        "by its index from the listed legal options. Submit a choice for every unit "
        "using the submit_order_choices tool.\n\n" + "\n".join(lines)
    )


def request_choices(grouped):
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=settings.BOT_LLM_MODEL,
        max_tokens=1024,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": build_prompt(grouped)}],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            return {choice["source_id"]: choice["option_index"] for choice in block.input["choices"]}
    raise ValueError("no submit_order_choices tool use in response")


def select_orders(options):
    if not settings.ANTHROPIC_API_KEY:
        logger.info("[bot.llm] no ANTHROPIC_API_KEY set; using first-legal selection")
        return first_legal_selections(options)

    grouped = group_by_source(options)
    logger.info(f"[bot.llm] asking {settings.BOT_LLM_MODEL} to choose orders for {len(grouped)} unit(s)")
    try:
        choices = request_choices(grouped)
    except Exception as e:
        logger.error(f"[bot.llm] order selection failed: {e}; falling back to first-legal")
        return first_legal_selections(options)

    selections = []
    for source_id, source_options in grouped.items():
        index = choices.get(source_id)
        if index is None or not (0 <= index < len(source_options)):
            chosen = source_options[0]
            logger.info(f"[bot.llm] {source_id}: invalid/missing choice {index}; using first legal option {option_label(chosen)}")
        else:
            chosen = source_options[index]
            logger.info(f"[bot.llm] {source_id}: chose {option_label(chosen)}")
        selections.append(option_to_selected(chosen))
    logger.info(f"[bot.llm] selected {len(selections)} order(s) via {settings.BOT_LLM_MODEL}")
    return selections
