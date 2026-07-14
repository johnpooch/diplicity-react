import logging

from anthropic import Anthropic
from django.conf import settings

from inference.clients.base import InferenceResult
from inference.exceptions import InferenceError

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 2048


class AnthropicInferenceClient:
    def __init__(self, api_key):
        if not api_key:
            raise InferenceError("BOT_ANTHROPIC_API_KEY is not set")
        self._client = Anthropic(api_key=api_key)

    def complete(self, *, model, system, messages, output_schema=None, max_tokens=None):
        logger.info(f"[inference.anthropic] completing via {model}")
        create_kwargs = dict(
            model=model,
            max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
            system=system,
            messages=messages,
        )
        if output_schema is not None and settings.BOT_LLM_STRUCTURED_OUTPUTS:
            create_kwargs["output_config"] = {
                "format": {"type": "json_schema", "schema": output_schema}
            }
        try:
            message = self._client.messages.create(**create_kwargs)
        except Exception as e:
            raise InferenceError(f"request failed: {e}") from e

        text = "".join(block.text for block in message.content if block.type == "text")
        if not text:
            raise InferenceError("no text content in response")

        usage = message.usage
        return InferenceResult(
            text=text,
            model=message.model,
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cache_read_tokens=usage.cache_read_input_tokens or 0,
            cache_write_tokens=usage.cache_creation_input_tokens or 0,
        )
