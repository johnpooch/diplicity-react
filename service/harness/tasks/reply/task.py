import logging

from harness.blocks import ChannelMessagesBlock, GameStateBlock, IdentityBlock
from harness.resources import load_prompt
from harness.tasks.base import TaskDefinition, extract_json
from harness.tasks.reply.schema import REPLY_SCHEMA
from harness.types import ContextData

logger = logging.getLogger(__name__)


class ReplyTask(TaskDefinition):
    name = "reply"
    system_prompt = load_prompt(__package__, "system.txt")
    instruction = load_prompt(__package__, "instruction.txt")
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
