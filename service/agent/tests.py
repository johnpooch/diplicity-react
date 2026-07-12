import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from agent import decorators, tasks
from agent.api_client import bot_request_host
from agent.fallback import first_legal_selections
from bot_profile.models import BotProfile
from bot_profile.utils import get_bot_user
from channel.models import ChannelMessage
from common.constants import OrderType
from inference.clients.base import InferenceResult
from inference.constants import InferenceStatus
from inference.models import Inference


def _option(source, order_type, target=None, aux=None, unit_type=None, named_coast=None):
    def field(value):
        return {"id": value, "label": value} if value is not None else None

    return {
        "source": field(source),
        "order_type": field(order_type),
        "target": field(target),
        "aux": field(aux),
        "unit_type": field(unit_type),
        "named_coast": field(named_coast),
    }


def _inference_result(text):
    return InferenceResult(
        text=text,
        model="test-model",
        input_tokens=100,
        output_tokens=20,
        cache_read_tokens=50,
        cache_write_tokens=5,
    )


def _mock_inference_client(text):
    client = Mock()
    client.complete.return_value = _inference_result(text)
    return client


def _reply_response(message):
    return json.dumps({"reasoning": "because", "message": message})


class TestFirstLegalSelections:

    def test_picks_first_option_per_source(self):
        options = [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
            _option("edi", OrderType.MOVE, target="nwg"),
            _option("edi", OrderType.HOLD),
        ]
        assert first_legal_selections(options) == [
            ["lon", OrderType.HOLD],
            ["edi", OrderType.MOVE, "nwg"],
        ]


class TestAdjustmentOrderLimit:

    def _options_with_three_builds(self):
        return {
            "orders": [
                _option("lon", OrderType.BUILD, unit_type="Army"),
                _option("edi", OrderType.BUILD, unit_type="Fleet"),
                _option("lvp", OrderType.BUILD, unit_type="Army"),
            ]
        }

    def _fake_client(self, max_orders):
        options = self._options_with_three_builds()

        def fake_get(url, *args, **kwargs):
            if "phase-states" in url:
                return Mock(status_code=200, data=[{"max_orders": max_orders}])
            if "channels" in url:
                return Mock(status_code=200, data=[])
            if url.endswith("/options/"):
                return Mock(status_code=200, data=options)
            return Mock(status_code=200, data={"phase_confirmed": False})

        client = MagicMock()
        client.get.side_effect = fake_get
        client.post.return_value = Mock(status_code=201)
        return client

    @pytest.mark.django_db
    def test_plan_caps_orders_at_max_orders(self):
        bot_user = get_bot_user()
        fake_client = self._fake_client(max_orders=1)

        with patch("agent.api_client.APIClient", return_value=fake_client):
            tasks.plan(user_id=bot_user.id, game_id="some-game")

        assert fake_client.post.call_count == 1

    @pytest.mark.django_db
    def test_plan_submits_all_orders_when_no_limit(self):
        bot_user = get_bot_user()
        fake_client = self._fake_client(max_orders=None)

        with patch("agent.api_client.APIClient", return_value=fake_client):
            tasks.plan(user_id=bot_user.id, game_id="some-game")

        assert fake_client.post.call_count == 3


class TestPlanTask:

    @pytest.mark.django_db
    def test_plan_creates_orders_without_confirming(
        self, bot_game_factory, in_memory_procrastinate
    ):
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)

        tasks.plan(user_id=bot_user.id, game_id=game.id)

        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders.count() > 0
        assert all(order.complete for order in bot_phase_state.orders.all())
        assert bot_phase_state.orders_confirmed is False

    @pytest.mark.django_db
    def test_plan_injects_persona_into_system_prompt(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game = bot_game_factory()
        bot_user = get_bot_user()
        disposition = BotProfile.objects.get(user=bot_user).disposition

        client = _mock_inference_client(json.dumps({"choices": []}))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        system = client.complete.call_args.kwargs["system"]
        assert disposition in system

    @pytest.mark.django_db
    def test_plan_records_success_inference(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)

        response = json.dumps(
            {"reasoning": "hold everything", "choices": [{"source_id": "rom", "option_index": 0}]}
        )
        client = _mock_inference_client(response)
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        inference = Inference.objects.get(task="select_orders")
        assert inference.status == InferenceStatus.SUCCEEDED
        assert inference.member == bot_member
        assert inference.phase == game.current_phase
        assert inference.model == "test-model"
        assert inference.output_tokens == 20
        assert inference.cache_read_tokens == 50

    @pytest.mark.django_db
    def test_plan_records_failed_inference_and_falls_back(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)

        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        inference = Inference.objects.get(task="select_orders")
        assert inference.status == InferenceStatus.FAILED
        assert inference.error_message
        assert inference.input_tokens == 0
        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders.count() > 0

    @pytest.mark.django_db
    def test_plan_falls_back_when_parse_fails(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)

        client = _mock_inference_client("not json at all")
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders.count() > 0

    @pytest.mark.django_db
    def test_plan_creates_orders_when_testserver_not_allowed(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ALLOWED_HOSTS = ["example.com"]
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)

        tasks.plan(user_id=bot_user.id, game_id=game.id)

        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders.count() > 0


class TestBotRequestHost:

    def test_returns_first_concrete_host(self, settings):
        settings.ALLOWED_HOSTS = ["example.com", "localhost"]
        assert bot_request_host() == "example.com"

    def test_strips_leading_dot(self, settings):
        settings.ALLOWED_HOSTS = [".railway.app"]
        assert bot_request_host() == "railway.app"

    def test_falls_back_to_testserver_for_wildcard(self, settings):
        settings.ALLOWED_HOSTS = ["*"]
        assert bot_request_host() == "testserver"


class TestBotIdentificationByProfile:

    @pytest.mark.django_db
    def test_bot_user_ids_for_phase_ignores_email(self, phase_factory, classical_england_nation):
        bot_user = get_bot_user()
        bot_user.email = "not-the-magic-email@example.com"
        bot_user.save()
        phase = phase_factory(
            phase_states_config=[{"nation": classical_england_nation, "user": bot_user}]
        )

        assert decorators._bot_user_ids_for_phase(phase.id) == {bot_user.id}

    @pytest.mark.django_db
    def test_roster_bots_are_identified_as_bots(self, phase_factory, classical_england_nation):
        roster_user = BotProfile.objects.exclude(user=get_bot_user()).first().user
        phase = phase_factory(
            phase_states_config=[{"nation": classical_england_nation, "user": roster_user}]
        )

        assert roster_user.id in decorators._bot_user_ids_for_phase(phase.id)


class TestFinalizeTask:

    @pytest.mark.django_db
    def test_finalize_submits_and_confirms(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)

        tasks.finalize(user_id=bot_user.id, game_id=game.id)

        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders.count() > 0
        assert bot_phase_state.orders_confirmed is True

    @pytest.mark.django_db
    def test_finalize_does_not_double_toggle_when_confirmed(
        self, bot_game_factory, in_memory_procrastinate
    ):
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_phase_state = game.current_phase.phase_states.get(member__user=bot_user)

        tasks.finalize(user_id=bot_user.id, game_id=game.id)
        tasks.finalize(user_id=bot_user.id, game_id=game.id)

        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders_confirmed is True


def _agent_plan_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "agent.plan"]


def _agent_finalize_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "agent.finalize"]


def _agent_reply_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "agent.reply"]


class TestPlanTrigger:

    @pytest.mark.django_db
    def test_first_phase_activation_defers_plan(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        bot_member = game.members.get(user=get_bot_user())

        jobs = _agent_plan_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["lock"] == f"plan-{game.current_phase.id}-{bot_member.id}"
        assert jobs[0]["args"] == {"user_id": get_bot_user().id, "game_id": game.id}

    @pytest.mark.django_db
    def test_editing_active_phase_does_not_refire(
        self, bot_game_factory, in_memory_procrastinate
    ):
        game = bot_game_factory()
        phase = game.current_phase

        phase.refresh_from_db()
        phase.save()

        assert len(_agent_plan_jobs(in_memory_procrastinate)) == 1

    @pytest.mark.django_db
    def test_non_bot_game_does_not_defer_plan(self, active_game_factory, in_memory_procrastinate):
        active_game_factory()
        assert len(_agent_plan_jobs(in_memory_procrastinate)) == 0


class TestFinalizeTrigger:

    @pytest.mark.django_db
    def test_human_confirm_defers_finalize(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        bot_member = game.members.get(user=get_bot_user())

        human_client = APIClient()
        human_client.force_authenticate(user=game.created_by)
        response = human_client.put(reverse("game-confirm-phase", args=[game.id]))
        assert response.status_code == status.HTTP_200_OK

        jobs = _agent_finalize_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["lock"] == f"finalize-{game.current_phase.id}-{bot_member.id}"
        assert jobs[0]["args"] == {"user_id": get_bot_user().id, "game_id": game.id}


class TestReplyTask:

    @pytest.mark.django_db
    def test_reply_posts_message_in_private_channel(
        self, bot_private_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_private_channel_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Just between us")

        client = _mock_inference_client(_reply_response("Understood."))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        assert channel.messages.filter(sender=bot_member, body="Understood.").exists()

    @pytest.mark.django_db
    def test_reply_records_inference_with_channel(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")

        client = _mock_inference_client(_reply_response("Hello, human!"))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        inference = Inference.objects.get(task="reply")
        assert inference.channel_id == channel.id
        assert inference.member == game.members.get(user=bot_user)

    @pytest.mark.django_db
    def test_reply_truncates_message_over_char_limit(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")

        overlong = "x" * (settings.CHAT_MESSAGE_MAX_CHARS + 50)
        client = _mock_inference_client(_reply_response(overlong))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        message = channel.messages.get(sender=bot_member)
        assert len(message.body) == settings.CHAT_MESSAGE_MAX_CHARS

    @pytest.mark.django_db
    def test_reply_posts_nothing_when_message_empty(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")

        client = _mock_inference_client(_reply_response("   "))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        assert channel.messages.filter(sender__user=bot_user).count() == 0

    @pytest.mark.django_db
    def test_reply_posts_nothing_when_inference_fails(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")

        with patch("inference.clients.anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        assert channel.messages.filter(sender__user=bot_user).count() == 0

    @pytest.mark.django_db
    def test_reply_skips_inference_when_message_cap_reached(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)
        for i in range(settings.BOT_CHANNEL_MESSAGE_CAP):
            ChannelMessage.objects.create(
                channel=channel, sender=bot_member, body=f"msg {i}", phase=game.current_phase
            )

        client = _mock_inference_client(_reply_response("too chatty"))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)
            client.complete.assert_not_called()

        assert channel.messages.filter(sender=bot_member).count() == settings.BOT_CHANNEL_MESSAGE_CAP

    @pytest.mark.django_db
    def test_reply_injects_persona_into_system_prompt(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")
        disposition = BotProfile.objects.get(user=bot_user).disposition

        client = _mock_inference_client(_reply_response("Hello."))
        with patch("inference.models.get_inference_client", return_value=client):
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        system = client.complete.call_args.kwargs["system"]
        assert disposition in system
        assert "Voice governs how you communicate" in system


class TestReplyTrigger:

    @pytest.mark.django_db
    def test_human_public_message_defers_reply(
        self, bot_public_channel_factory, in_memory_procrastinate
    ):
        game, channel = bot_public_channel_factory()
        bot_member = game.members.get(user=get_bot_user())

        human_client = APIClient()
        human_client.force_authenticate(user=game.created_by)
        response = human_client.post(
            reverse("channel-message-create", args=[game.id, channel.id]),
            {"body": "Hello bot"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        jobs = _agent_reply_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["lock"] == f"reply-{response.data['id']}-{bot_member.id}"
        assert jobs[0]["args"] == {
            "user_id": get_bot_user().id,
            "game_id": game.id,
            "channel_id": channel.id,
        }

    @pytest.mark.django_db
    def test_bot_own_message_does_not_defer_reply(
        self, bot_public_channel_factory, in_memory_procrastinate
    ):
        game, channel = bot_public_channel_factory()
        bot_member = game.members.get(user=get_bot_user())

        ChannelMessage.objects.create(channel=channel, sender=bot_member, body="Hi all")

        assert len(_agent_reply_jobs(in_memory_procrastinate)) == 0

    @pytest.mark.django_db
    def test_private_channel_message_defers_reply(
        self, bot_public_channel_factory, in_memory_procrastinate
    ):
        game, _ = bot_public_channel_factory()
        bot_member = game.members.get(user=get_bot_user())
        human_member = game.members.get(user=game.created_by)
        private = game.channels.create(name="Private", private=True)
        private.member_channels.create(member=bot_member)
        private.member_channels.create(member=human_member)

        human_client = APIClient()
        human_client.force_authenticate(user=game.created_by)
        response = human_client.post(
            reverse("channel-message-create", args=[game.id, private.id]),
            {"body": "Just between us"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        jobs = _agent_reply_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["lock"] == f"reply-{response.data['id']}-{bot_member.id}"
        assert jobs[0]["args"] == {
            "user_id": get_bot_user().id,
            "game_id": game.id,
            "channel_id": private.id,
        }

    @pytest.mark.django_db
    def test_private_channel_without_bot_member_does_not_defer_reply(
        self, bot_public_channel_factory, in_memory_procrastinate, secondary_user
    ):
        game, _ = bot_public_channel_factory()
        human_member = game.members.get(user=game.created_by)
        other_member = game.members.create(user=secondary_user)
        private = game.channels.create(name="Private", private=True)
        private.member_channels.create(member=human_member)
        private.member_channels.create(member=other_member)

        human_client = APIClient()
        human_client.force_authenticate(user=game.created_by)
        response = human_client.post(
            reverse("channel-message-create", args=[game.id, private.id]),
            {"body": "No bots here"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        assert len(_agent_reply_jobs(in_memory_procrastinate)) == 0

    @pytest.mark.django_db
    def test_non_bot_game_does_not_defer_reply(
        self, active_game_factory, in_memory_procrastinate
    ):
        game = active_game_factory()
        channel = game.channels.create(name="Public Press", private=False)
        member = game.members.get(user=game.created_by)
        channel.member_channels.create(member=member)

        human_client = APIClient()
        human_client.force_authenticate(user=game.created_by)
        response = human_client.post(
            reverse("channel-message-create", args=[game.id, channel.id]),
            {"body": "Anyone there?"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        assert len(_agent_reply_jobs(in_memory_procrastinate)) == 0
