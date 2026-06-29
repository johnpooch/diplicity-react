import logging

from anthropic import Anthropic
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, api_key):
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        self._client = Anthropic(api_key=api_key)

    def run(self, action):
        logger.info(f"[bot.llm] running {action.name} via {settings.BOT_LLM_MODEL}")
        try:
            message = self._client.messages.create(
                model=settings.BOT_LLM_MODEL,
                max_tokens=1024,
                system=action.system,
                tools=[action.tool],
                tool_choice={"type": "tool", "name": action.tool["name"]},
                messages=action.build_messages(),
            )
        except Exception as e:
            raise LLMError(f"{action.name} request failed: {e}") from e

        for block in message.content:
            if block.type == "tool_use" and block.name == action.tool["name"]:
                return action.parse(block.input)
        raise LLMError(f"no {action.tool['name']} tool use in response")
