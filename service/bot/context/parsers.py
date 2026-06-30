import json
import logging

from bot.context.orders import (
    group_options_by_source,
    option_to_selected,
    order_option_label,
)
from bot.llm_client import LLMError
from bot.types import OrderOptionDict

logger = logging.getLogger(__name__)


def _extract_json(response_text: str) -> dict:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"could not parse JSON from response: {e}") from e


def parse_order_selections(
    response_text: str, options: list[OrderOptionDict]
) -> list[list[str]]:
    data = _extract_json(response_text)

    choices = {}
    for choice in data.get("choices", []):
        if isinstance(choice, dict) and "source_id" in choice and "option_index" in choice:
            choices[choice["source_id"]] = choice["option_index"]

    selections = []
    for source_id, source_options in group_options_by_source(options).items():
        index = choices.get(source_id)
        if index is None or not (0 <= index < len(source_options)):
            chosen = source_options[0]
            logger.info(
                f"[bot.llm] {source_id}: invalid/missing choice {index}; "
                f"using first legal option {order_option_label(chosen)}"
            )
        else:
            chosen = source_options[index]
            logger.info(f"[bot.llm] {source_id}: chose {order_option_label(chosen)}")
        selections.append(option_to_selected(chosen))
    logger.info(f"[bot.llm] selected {len(selections)} order(s)")
    return selections


def parse_reply(response_text: str) -> str | None:
    data = _extract_json(response_text)
    if not data.get("should_reply"):
        logger.info("[bot.llm] model declined to reply")
        return None
    reply = (data.get("message") or "").strip()
    if not reply:
        logger.info("[bot.llm] model returned empty reply; staying silent")
        return None
    logger.info(f"[bot.llm] composed chat reply ({len(reply)} char(s))")
    return reply
