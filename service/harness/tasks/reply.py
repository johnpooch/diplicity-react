import logging

from harness.blocks import ChannelMessagesBlock, GameStateBlock, IdentityBlock
from harness.prompts import load_prompt
from harness.tasks.base import TaskDefinition, extract_json
from harness.types import ContextData

logger = logging.getLogger(__name__)

REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["reasoning", "message"],
    "additionalProperties": False,
}


class ReplyTask(TaskDefinition):
    name = "reply"
    system_prompt = load_prompt("reply_system.txt")
    instruction = load_prompt("reply_instruction.txt")
    blocks = (GameStateBlock(), IdentityBlock(), ChannelMessagesBlock())
    output_schema = REPLY_SCHEMA

    @classmethod
    def parse(cls, response: str, *, context: ContextData) -> str | None:
        data = extract_json(response)
        reasoning = data.get("reasoning")
        if reasoning:
            logger.info(f"[harness.reply] reasoning: {reasoning}")
        message = (data.get("message") or "").strip()
        if not message:
            logger.info("[harness.reply] empty message; nothing to send")
            return None
        logger.info(f"[harness.reply] composed chat reply ({len(message)} char(s))")
        return message
