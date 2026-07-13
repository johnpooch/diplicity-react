from django.conf import settings

from inference.clients.anthropic import AnthropicInferenceClient
from inference.constants import InferenceProvider
from inference.exceptions import InferenceError


def get_inference_client(provider):
    if provider == InferenceProvider.ANTHROPIC:
        return AnthropicInferenceClient(settings.ANTHROPIC_API_KEY)
    raise InferenceError(f"unknown inference provider: {provider}")
