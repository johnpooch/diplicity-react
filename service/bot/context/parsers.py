from bot.llm_client import LLMError
from bot.steps import (
    ORDER_SELECTION_SCHEMA,
    REPLY_SCHEMA,
    reply_from_verdict,
    selections_from_order_verdict,
    validate_order_selections,
    validate_reply,
)
from bot.types import OrderOptionDict

__all__ = [
    "ORDER_SELECTION_SCHEMA",
    "REPLY_SCHEMA",
    "parse_order_selections",
    "parse_reply",
]


def parse_order_selections(
    response_text: str, options: list[OrderOptionDict]
) -> list[list[str]]:
    verdict = validate_order_selections(response_text, options)
    if verdict["parse_error"] is not None:
        raise LLMError(verdict["parse_error"])
    return selections_from_order_verdict(verdict, options)


def parse_reply(response_text: str) -> str | None:
    verdict = validate_reply(response_text)
    if verdict["parse_error"] is not None:
        raise LLMError(verdict["parse_error"])
    return reply_from_verdict(verdict)
