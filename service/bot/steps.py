import json
import logging
from typing import Callable, TypedDict

from bot.context.builder import ContextBuilder
from bot.context.orders import (
    group_options_by_source,
    option_to_selected,
    order_option_label,
)
from bot.llm_client import LLMError
from bot.prompts import load_prompt
from bot.types import ContextData, OrderOptionDict

logger = logging.getLogger(__name__)

Complete = Callable[..., str]

ORDER_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
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
        },
    },
    "required": ["reasoning", "choices"],
    "additionalProperties": False,
}

REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "should_reply": {"type": "boolean"},
        "message": {"type": "string"},
    },
    "required": ["reasoning", "should_reply"],
    "additionalProperties": False,
}


class OrderSourceVerdict(TypedDict):
    source_id: str
    index: int | None
    status: str


class OrderVerdict(TypedDict):
    parsed: bool
    parse_error: str | None
    reasoning: str
    choices: dict[str, int]
    sources: list[OrderSourceVerdict]
    duplicate_source_ids: list[str]
    unknown_source_ids: list[str]
    malformed_choices: list[object]


class ReplyVerdict(TypedDict):
    parsed: bool
    parse_error: str | None
    reasoning: str
    should_reply: bool
    message: str
    empty: bool


class SelectOrdersResult(TypedDict):
    response_text: str
    verdict: OrderVerdict


class ReplyResult(TypedDict):
    response_text: str
    verdict: ReplyVerdict


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


def build_select_orders_prompt(
    data: ContextData, persona: str = ""
) -> tuple[str, list[dict]]:
    builder = (
        ContextBuilder(data)
        .with_game_state()
        .with_tactical_annotations()
        .with_identity()
        .with_orders()
        .with_phase_state()
        .with_conversations()
    )
    system = load_prompt("select_orders_system.txt")
    if persona:
        system = f"{system}\n\n{persona}"
    instruction = load_prompt("select_orders_instruction.txt")
    user_content = "\n\n".join(
        part for part in [builder.build_shared(), builder.build_private(), instruction] if part
    )
    return system, [{"role": "user", "content": user_content}]


def build_reply_prompt(
    data: ContextData, persona: str = "", channel_id=None
) -> tuple[str, list[dict]]:
    builder = (
        ContextBuilder(data)
        .with_game_state()
        .with_tactical_annotations()
        .with_identity()
        .with_messages(channel_id=channel_id)
    )
    system = load_prompt("reply_system.txt")
    if persona:
        system = f"{system}\n\n{persona}"
    instruction = load_prompt("reply_instruction.txt")
    user_content = "\n\n".join(
        part for part in [builder.build_shared(), builder.build_private(), instruction] if part
    )
    return system, [{"role": "user", "content": user_content}]


def validate_order_selections(
    response_text: str, options: list[OrderOptionDict]
) -> OrderVerdict:
    try:
        data = _extract_json(response_text)
    except LLMError as e:
        return OrderVerdict(
            parsed=False,
            parse_error=str(e),
            reasoning="",
            choices={},
            sources=[],
            duplicate_source_ids=[],
            unknown_source_ids=[],
            malformed_choices=[],
        )

    choices: dict[str, int] = {}
    duplicate_source_ids: list[str] = []
    malformed_choices: list[object] = []
    for choice in data.get("choices", []):
        if isinstance(choice, dict) and "source_id" in choice and "option_index" in choice:
            source_id = choice["source_id"]
            if source_id in choices:
                duplicate_source_ids.append(source_id)
            choices[source_id] = choice["option_index"]
        else:
            malformed_choices.append(choice)

    grouped = group_options_by_source(options)
    sources: list[OrderSourceVerdict] = []
    for source_id, source_options in grouped.items():
        index = choices.get(source_id)
        if index is None:
            status = "missing"
        elif not (0 <= index < len(source_options)):
            status = "out_of_range"
        else:
            status = "valid"
        sources.append(OrderSourceVerdict(source_id=source_id, index=index, status=status))

    unknown_source_ids = [source_id for source_id in choices if source_id not in grouped]

    return OrderVerdict(
        parsed=True,
        parse_error=None,
        reasoning=str(data.get("reasoning") or ""),
        choices=choices,
        sources=sources,
        duplicate_source_ids=duplicate_source_ids,
        unknown_source_ids=unknown_source_ids,
        malformed_choices=malformed_choices,
    )


def selections_from_order_verdict(
    verdict: OrderVerdict, options: list[OrderOptionDict]
) -> list[list[str]]:
    if verdict["reasoning"]:
        logger.info(f"[bot.llm] order reasoning: {verdict['reasoning']}")
    grouped = group_options_by_source(options)
    selections = []
    for source in verdict["sources"]:
        source_id = source["source_id"]
        source_options = grouped[source_id]
        index = source["index"]
        if source["status"] == "valid":
            chosen = source_options[index]
            logger.info(f"[bot.llm] {source_id}: chose {order_option_label(chosen)}")
        else:
            chosen = source_options[0]
            logger.info(
                f"[bot.llm] {source_id}: invalid/missing choice {index}; "
                f"using first legal option {order_option_label(chosen)}"
            )
        selections.append(option_to_selected(chosen))
    logger.info(f"[bot.llm] selected {len(selections)} order(s)")
    return selections


def validate_reply(response_text: str) -> ReplyVerdict:
    try:
        data = _extract_json(response_text)
    except LLMError as e:
        return ReplyVerdict(
            parsed=False,
            parse_error=str(e),
            reasoning="",
            should_reply=False,
            message="",
            empty=True,
        )

    should_reply = bool(data.get("should_reply"))
    message = (data.get("message") or "").strip()
    return ReplyVerdict(
        parsed=True,
        parse_error=None,
        reasoning=str(data.get("reasoning") or ""),
        should_reply=should_reply,
        message=message,
        empty=not message,
    )


def reply_from_verdict(verdict: ReplyVerdict) -> str | None:
    if verdict["reasoning"]:
        logger.info(f"[bot.llm] reply reasoning: {verdict['reasoning']}")
    if not verdict["should_reply"]:
        logger.info("[bot.llm] model declined to reply")
        return None
    if verdict["empty"]:
        logger.info("[bot.llm] model returned empty reply; staying silent")
        return None
    logger.info(f"[bot.llm] composed chat reply ({len(verdict['message'])} char(s))")
    return verdict["message"]


def run_select_orders(
    data: ContextData, persona: str, complete: Complete
) -> SelectOrdersResult:
    system, messages = build_select_orders_prompt(data, persona)
    response_text = complete(
        system=system, messages=messages, output_schema=ORDER_SELECTION_SCHEMA
    )
    verdict = validate_order_selections(response_text, data["orders"])
    return SelectOrdersResult(response_text=response_text, verdict=verdict)


def run_reply(
    data: ContextData, persona: str, channel_id, complete: Complete
) -> ReplyResult:
    system, messages = build_reply_prompt(data, persona, channel_id=channel_id)
    response_text = complete(
        system=system, messages=messages, output_schema=REPLY_SCHEMA
    )
    verdict = validate_reply(response_text)
    return ReplyResult(response_text=response_text, verdict=verdict)
