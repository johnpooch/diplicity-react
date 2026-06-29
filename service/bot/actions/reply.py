import logging

from bot.actions.base import Action

logger = logging.getLogger(__name__)

TOOL_NAME = "reply_to_chat"

TOOL = {
    "name": TOOL_NAME,
    "description": "Decide whether to reply to the conversation, and provide the reply text.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "should_reply": {"type": "boolean"},
            "message": {"type": "string"},
        },
        "required": ["should_reply", "message"],
        "additionalProperties": False,
    },
}

PROMPT_PREAMBLE = (
    "You are a player in a game of Diplomacy, taking part in the public chat with the "
    'other players. Below is the conversation so far, where "You" marks your own '
    "previous messages. Decide whether to send a reply. Only reply if a reply is "
    "warranted and you have something worth saying; staying silent is a perfectly good "
    "choice. Keep any reply short, on-topic, and in the spirit of friendly table talk. "
    "Use the reply_to_chat tool to respond."
)


class ReplyAction(Action):
    name = "reply"
    tool = TOOL

    def __init__(self, messages):
        self.messages = messages

    def build_prompt(self):
        lines = [f"{message.speaker}: {message.body}" for message in self.messages]
        return PROMPT_PREAMBLE + "\n\n" + "\n".join(lines)

    def parse(self, tool_input):
        if not tool_input.get("should_reply"):
            logger.info("[bot.llm] model declined to reply")
            return None
        reply = (tool_input.get("message") or "").strip()
        if not reply:
            logger.info("[bot.llm] model returned empty reply; staying silent")
            return None
        logger.info(f"[bot.llm] composed chat reply ({len(reply)} char(s))")
        return reply

    def fallback(self):
        return None
