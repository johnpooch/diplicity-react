import logging

from anthropic import Anthropic
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def run(self, action):
        if not settings.ANTHROPIC_API_KEY:
            logger.info(
                f"[bot.llm] no ANTHROPIC_API_KEY set; using fallback for {action.name}"
            )
            return action.fallback()

        logger.info(f"[bot.llm] running {action.name} via {settings.BOT_LLM_MODEL}")
        try:
            tool_input = self._invoke(action)
        except Exception as e:
            logger.error(f"[bot.llm] {action.name} failed: {e}; using fallback")
            return action.fallback()

        return action.parse(tool_input)

    def _invoke(self, action):
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=settings.BOT_LLM_MODEL,
            max_tokens=1024,
            tools=[action.tool],
            tool_choice={"type": "tool", "name": action.tool["name"]},
            messages=[{"role": "user", "content": action.build_prompt()}],
        )
        for block in message.content:
            if block.type == "tool_use" and block.name == action.tool["name"]:
                return block.input
        raise ValueError(f"no {action.tool['name']} tool use in response")
