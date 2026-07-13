from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from django.utils import timezone

from inference.clients.anthropic import AnthropicInferenceClient
from inference.clients.base import InferenceResult
from inference.clients.registry import get_inference_client
from inference.constants import InferenceProvider, InferenceStatus
from inference.exceptions import InferenceError
from inference.models import Inference


def _anthropic_message(text):
    block = Mock(type="text", text=text)
    usage = Mock(
        input_tokens=120,
        output_tokens=45,
        cache_read_input_tokens=80,
        cache_creation_input_tokens=10,
    )
    return Mock(content=[block], model="test-model", usage=usage)


SCHEMA = {"type": "object", "properties": {}, "additionalProperties": False}


class TestAnthropicInferenceClient:

    def test_raises_without_key(self):
        with pytest.raises(InferenceError):
            AnthropicInferenceClient("")

    def test_raises_when_request_fails(self):
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            with pytest.raises(InferenceError):
                AnthropicInferenceClient("test-key").complete(
                    model="m", system="s", messages=[{"role": "user", "content": "x"}]
                )

    def test_raises_when_no_text_content(self):
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = Mock(
                content=[], model="test-model", usage=Mock()
            )
            with pytest.raises(InferenceError):
                AnthropicInferenceClient("test-key").complete(
                    model="m", system="s", messages=[{"role": "user", "content": "x"}]
                )

    def test_returns_result_with_usage(self):
        block_one = Mock(type="text", text="Hello, ")
        block_two = Mock(type="text", text="human!")
        usage = Mock(
            input_tokens=120,
            output_tokens=45,
            cache_read_input_tokens=80,
            cache_creation_input_tokens=10,
        )
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = Mock(
                content=[block_one, block_two], model="test-model", usage=usage
            )
            result = AnthropicInferenceClient("test-key").complete(
                model="m", system="s", messages=[{"role": "user", "content": "x"}]
            )
        assert result == InferenceResult(
            text="Hello, human!",
            model="test-model",
            input_tokens=120,
            output_tokens=45,
            cache_read_tokens=80,
            cache_write_tokens=10,
        )

    @override_settings(BOT_LLM_STRUCTURED_OUTPUTS=True)
    def test_passes_output_config_when_schema_provided_and_enabled(self):
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            create = mock_anthropic.return_value.messages.create
            create.return_value = _anthropic_message("ok")
            AnthropicInferenceClient("test-key").complete(
                model="m",
                system="s",
                messages=[{"role": "user", "content": "x"}],
                output_schema=SCHEMA,
            )
        assert create.call_args.kwargs["output_config"] == {
            "format": {"type": "json_schema", "schema": SCHEMA}
        }

    @override_settings(BOT_LLM_STRUCTURED_OUTPUTS=False)
    def test_omits_output_config_when_structured_outputs_disabled(self):
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            create = mock_anthropic.return_value.messages.create
            create.return_value = _anthropic_message("ok")
            AnthropicInferenceClient("test-key").complete(
                model="m",
                system="s",
                messages=[{"role": "user", "content": "x"}],
                output_schema=SCHEMA,
            )
        assert "output_config" not in create.call_args.kwargs

    @override_settings(BOT_LLM_STRUCTURED_OUTPUTS=True)
    def test_omits_output_config_when_no_schema(self):
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            create = mock_anthropic.return_value.messages.create
            create.return_value = _anthropic_message("ok")
            AnthropicInferenceClient("test-key").complete(
                model="m", system="s", messages=[{"role": "user", "content": "x"}]
            )
        assert "output_config" not in create.call_args.kwargs

    def test_passes_max_tokens(self):
        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            create = mock_anthropic.return_value.messages.create
            create.return_value = _anthropic_message("ok")
            AnthropicInferenceClient("test-key").complete(
                model="m",
                system="s",
                messages=[{"role": "user", "content": "x"}],
                max_tokens=512,
            )
        assert create.call_args.kwargs["max_tokens"] == 512


class TestRegistry:

    def test_returns_anthropic_client(self, settings):
        settings.ANTHROPIC_API_KEY = "test-key"
        client = get_inference_client(InferenceProvider.ANTHROPIC)
        assert isinstance(client, AnthropicInferenceClient)

    def test_raises_for_unknown_provider(self):
        with pytest.raises(InferenceError):
            get_inference_client("openai")


@pytest.fixture
def phase_with_member(phase_factory, classical_england_nation):
    phase = phase_factory(
        phase_states_config=[{"nation": classical_england_nation, "has_possible_orders": True}]
    )
    return phase, phase.phase_states.get().member


class TestInferenceModel:

    @pytest.mark.django_db
    def test_records_call_with_usage_and_text(self, phase_with_member):
        phase, member = phase_with_member

        inference = Inference.objects.create(
            phase=phase,
            member=member,
            task="select_orders",
            status=InferenceStatus.SUCCEEDED,
            model="claude-haiku",
            system="system prompt",
            user_content="user content",
            response="response text",
            input_tokens=120,
            output_tokens=45,
            cache_read_tokens=80,
            cache_write_tokens=10,
        )

        inference.refresh_from_db()
        assert inference.status == InferenceStatus.SUCCEEDED
        assert inference.input_tokens == 120
        assert inference.cache_read_tokens == 80
        assert inference.response == "response text"
        assert inference in phase.inferences.all()

    @pytest.mark.django_db
    def test_member_is_optional(self, phase_with_member):
        phase, _ = phase_with_member

        inference = Inference.objects.create(
            phase=phase, task="reply", model="claude-haiku"
        )

        inference.refresh_from_db()
        assert inference.member is None
        assert inference.input_tokens == 0
        assert inference.system == ""
        assert inference.status == InferenceStatus.PENDING

    def test_latency_ms_computed_from_timestamps(self):
        started = timezone.now()
        inference = Inference(started_at=started, completed_at=started + timedelta(milliseconds=120))
        assert inference.latency_ms == 120

    def test_latency_ms_none_without_timestamps(self):
        assert Inference(started_at=timezone.now()).latency_ms is None
        assert Inference().latency_ms is None


class TestInferenceRun:

    def _result(self):
        return InferenceResult(
            text="response text",
            model="resolved-model",
            input_tokens=120,
            output_tokens=45,
            cache_read_tokens=80,
            cache_write_tokens=10,
        )

    @pytest.mark.django_db
    def test_persists_succeeded_call(self, phase_with_member):
        phase, member = phase_with_member

        with patch("inference.models.get_inference_client") as mock_get_client:
            mock_get_client.return_value.complete.return_value = self._result()
            inference = Inference.objects.run(
                provider=InferenceProvider.ANTHROPIC,
                model="claude-haiku",
                task="select_orders",
                system="system prompt",
                user_content="user content",
                phase=phase,
                member=member,
            )

        inference.refresh_from_db()
        assert inference.status == InferenceStatus.SUCCEEDED
        assert inference.task == "select_orders"
        assert inference.model == "resolved-model"
        assert inference.response == "response text"
        assert inference.input_tokens == 120
        assert inference.cache_write_tokens == 10
        assert inference.started_at is not None
        assert inference.completed_at is not None
        assert inference.member == member

    @pytest.mark.django_db
    def test_persists_failed_call_and_reraises(self, phase_with_member):
        phase, member = phase_with_member

        with patch("inference.models.get_inference_client") as mock_get_client:
            mock_get_client.return_value.complete.side_effect = InferenceError("boom")
            with pytest.raises(InferenceError):
                Inference.objects.run(
                    provider=InferenceProvider.ANTHROPIC,
                    model="claude-haiku",
                    task="select_orders",
                    user_content="user content",
                    phase=phase,
                    member=member,
                )

        inference = Inference.objects.get()
        assert inference.status == InferenceStatus.FAILED
        assert inference.error_message == "boom"
        assert inference.response == ""
        assert inference.completed_at is not None

    @pytest.mark.django_db
    def test_joins_messages_into_user_content(self, phase_with_member):
        phase, _ = phase_with_member

        with patch("inference.models.get_inference_client") as mock_get_client:
            complete = mock_get_client.return_value.complete
            complete.return_value = self._result()
            inference = Inference.objects.run(
                provider=InferenceProvider.ANTHROPIC,
                model="claude-haiku",
                task="reply",
                messages=[
                    {"role": "user", "content": "first"},
                    {"role": "user", "content": "second"},
                ],
                phase=phase,
            )

        assert inference.user_content == "first\n\nsecond"
        assert complete.call_args.kwargs["messages"] == [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
        ]

    @pytest.mark.django_db
    def test_wraps_user_content_into_single_message(self, phase_with_member):
        phase, _ = phase_with_member

        with patch("inference.models.get_inference_client") as mock_get_client:
            complete = mock_get_client.return_value.complete
            complete.return_value = self._result()
            inference = Inference.objects.run(
                provider=InferenceProvider.ANTHROPIC,
                model="claude-haiku",
                task="reply",
                user_content="hello",
                phase=phase,
            )

        assert inference.user_content == "hello"
        assert complete.call_args.kwargs["messages"] == [{"role": "user", "content": "hello"}]

    @pytest.mark.django_db
    def test_passes_schema_and_max_tokens_to_client(self, phase_with_member):
        phase, _ = phase_with_member

        with patch("inference.models.get_inference_client") as mock_get_client:
            complete = mock_get_client.return_value.complete
            complete.return_value = self._result()
            Inference.objects.run(
                provider=InferenceProvider.ANTHROPIC,
                model="claude-haiku",
                task="select_orders",
                user_content="x",
                phase=phase,
                output_schema=SCHEMA,
                max_tokens=512,
            )

        assert complete.call_args.kwargs["output_schema"] == SCHEMA
        assert complete.call_args.kwargs["max_tokens"] == 512
