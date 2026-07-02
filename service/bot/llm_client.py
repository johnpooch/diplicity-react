import logging
import time

from anthropic import Anthropic
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, api_key, recorder):
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        self._client = Anthropic(api_key=api_key)
        self._recorder = recorder

    def complete(self, *, system, messages):
        logger.info(f"[bot.llm] completing via {settings.BOT_LLM_MODEL}")
        user_content = "\n\n".join(message["content"] for message in messages)
        start = time.monotonic()
        try:
            message = self._client.messages.create(
                model=settings.BOT_LLM_MODEL,
                max_tokens=1024,
                system=system,
                messages=messages,
            )
        except Exception as e:
            self._recorder.record_error(
                model=settings.BOT_LLM_MODEL,
                system=system,
                user_content=user_content,
                error_message=str(e),
                latency_ms=_elapsed_ms(start),
            )
            raise LLMError(f"request failed: {e}") from e

        text = "".join(block.text for block in message.content if block.type == "text")
        if not text:
            self._recorder.record_error(
                model=message.model,
                system=system,
                user_content=user_content,
                error_message="no text content in response",
                latency_ms=_elapsed_ms(start),
            )
            raise LLMError("no text content in response")

        usage = message.usage
        self._recorder.record_success(
            model=message.model,
            system=system,
            user_content=user_content,
            response=text,
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cache_read_tokens=usage.cache_read_input_tokens or 0,
            cache_write_tokens=usage.cache_creation_input_tokens or 0,
            latency_ms=_elapsed_ms(start),
        )
        return text


def _elapsed_ms(start):
    return int((time.monotonic() - start) * 1000)
