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

    def complete(self, *, system, messages):
        logger.info(f"[bot.llm] completing via {settings.BOT_LLM_MODEL}")
        try:
            message = self._client.messages.create(
                model=settings.BOT_LLM_MODEL,
                max_tokens=1024,
                system=system,
                messages=messages,
            )
        except Exception as e:
            raise LLMError(f"request failed: {e}") from e

        text = "".join(block.text for block in message.content if block.type == "text")
        if not text:
            raise LLMError("no text content in response")
        return text
