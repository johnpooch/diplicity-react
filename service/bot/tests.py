import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from adjudication import service as adjudication_service
from common.constants import (
    DeadlineMode,
    GameStatus,
    MovementPhaseDuration,
    NationAssignment,
    OrderType,
    PhaseStatus,
)
from channel.models import ChannelMessage
from game.models import Game
from bot.models import BotProfile, LLMCall
from bot import decorators, tasks, utils
from bot.constants import LLMCallStage, LLMCallStatus
from bot.context.builder import ContextBuilder
from bot.context.orders import first_legal_selections, option_to_selected
from bot.context.parsers import parse_order_selections, parse_reply
from bot.llm_client import LLMClient, LLMError
from bot.recorder import LLMCallRecorder
from bot.utils import get_bot_user


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


class TestOptionToSelected:

    def test_hold(self):
        assert option_to_selected(_option("lon", OrderType.HOLD)) == ["lon", OrderType.HOLD]

    def test_move(self):
        assert option_to_selected(_option("lon", OrderType.MOVE, target="nth")) == [
            "lon",
            OrderType.MOVE,
            "nth",
        ]

    def test_move_with_named_coast(self):
        assert option_to_selected(
            _option("mid", OrderType.MOVE, target="spa", named_coast="spa/nc")
        ) == ["mid", OrderType.MOVE, "spa", "spa/nc"]

    def test_support(self):
        assert option_to_selected(
            _option("lon", OrderType.SUPPORT, aux="wal", target="lvp")
        ) == ["lon", OrderType.SUPPORT, "wal", "lvp"]

    def test_build_fleet_named_coast(self):
        assert option_to_selected(
            _option("stp", OrderType.BUILD, unit_type="Fleet", named_coast="stp/sc")
        ) == ["stp", OrderType.BUILD, "Fleet", "stp/sc"]


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


class TestSelectOrders:

    def _options(self):
        return [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
            _option("edi", OrderType.HOLD),
            _option("edi", OrderType.MOVE, target="nwg"),
        ]

    def test_returns_llm_choice_per_source(self):
        response_text = json.dumps(
            {
                "choices": [
                    {"source_id": "lon", "option_index": 1},
                    {"source_id": "edi", "option_index": 1},
                ]
            }
        )
        assert parse_order_selections(response_text, self._options()) == [
            ["lon", OrderType.MOVE, "nth"],
            ["edi", OrderType.MOVE, "nwg"],
        ]

    def test_parses_json_wrapped_in_markdown_fence(self):
        response_text = (
            "```json\n"
            + json.dumps({"choices": [{"source_id": "lon", "option_index": 1}]})
            + "\n```"
        )
        assert parse_order_selections(response_text, self._options()) == [
            ["lon", OrderType.MOVE, "nth"],
            ["edi", OrderType.HOLD],
        ]

    def test_invalid_or_missing_index_falls_back_per_source(self):
        response_text = json.dumps({"choices": [{"source_id": "lon", "option_index": 9}]})
        assert parse_order_selections(response_text, self._options()) == [
            ["lon", OrderType.HOLD],
            ["edi", OrderType.HOLD],
        ]

    def test_raises_on_unparseable_json(self):
        with pytest.raises(LLMError):
            parse_order_selections("not json at all", self._options())


class TestLLMClient:

    def test_raises_without_key(self):
        with pytest.raises(LLMError):
            LLMClient("", Mock())

    def test_records_error_and_raises_when_client_raises(self):
        recorder = Mock()
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            with pytest.raises(LLMError):
                LLMClient("test-key", recorder).complete(
                    system="s", messages=[{"role": "user", "content": "x"}]
                )
        recorder.record_error.assert_called_once()
        recorder.record_success.assert_not_called()

    def test_returns_text_and_records_success(self):
        block_one = Mock(type="text", text="Hello, ")
        block_two = Mock(type="text", text="human!")
        usage = Mock(
            input_tokens=120,
            output_tokens=45,
            cache_read_input_tokens=80,
            cache_creation_input_tokens=10,
        )
        recorder = Mock()
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = Mock(
                content=[block_one, block_two], model="test-model", usage=usage
            )
            result = LLMClient("test-key", recorder).complete(
                system="s", messages=[{"role": "user", "content": "x"}]
            )
        assert result == "Hello, human!"
        recorder.record_success.assert_called_once()
        kwargs = recorder.record_success.call_args.kwargs
        assert kwargs["model"] == "test-model"
        assert kwargs["response"] == "Hello, human!"
        assert kwargs["input_tokens"] == 120
        assert kwargs["output_tokens"] == 45
        assert kwargs["cache_read_tokens"] == 80
        assert kwargs["cache_write_tokens"] == 10


class TestContextBuilder:

    def _data(self, channels=None, phase=None):
        return {
            "orders": [
                _option("lon", OrderType.HOLD),
                _option("lon", OrderType.MOVE, target="nth"),
            ],
            "phase_states": [{"max_orders": 3}],
            "game": {"phase_confirmed": False},
            "phase": phase if phase is not None else {},
            "channels": channels or [],
        }

    def _phase(self):
        def nation(name):
            return {"nation_id": name.lower(), "name": name}

        def province(province_id):
            return {"id": province_id, "name": province_id}

        return {
            "name": "Spring 1901, Movement",
            "type": "Movement",
            "units": [
                {"type": "Army", "nation": nation("England"), "province": province("lon"), "dislodged": False},
                {"type": "Fleet", "nation": nation("England"), "province": province("nth"), "dislodged": True},
                {"type": "Army", "nation": nation("France"), "province": province("par"), "dislodged": False},
            ],
            "supply_centers": [
                {"province": province("lon"), "nation": nation("England")},
                {"province": province("edi"), "nation": nation("England")},
                {"province": province("par"), "nation": nation("France")},
            ],
        }

    def test_with_game_state_groups_units_and_centers_by_nation(self):
        shared = ContextBuilder(self._data(phase=self._phase())).with_game_state().build_shared()
        assert "Current phase: Spring 1901, Movement" in shared
        assert "England: A lon, F nth (dislodged)" in shared
        assert "France: A par" in shared
        assert "England: 2 (edi, lon)" in shared
        assert "France: 1 (par)" in shared

    def test_with_game_state_empty_phase_is_noop(self):
        assert ContextBuilder(self._data()).with_game_state().build_shared() == ""

    def test_with_game_state_names_self_nation(self):
        data = self._data(phase=self._phase())
        data["game"]["members"] = [
            {"is_current_user": False, "nation": "England"},
            {"is_current_user": True, "nation": "France"},
        ]
        shared = ContextBuilder(data).with_game_state().build_shared()
        assert "You are playing France." in shared

    def _channel(self, channel_id, name, messages, private=False):
        return {"id": channel_id, "name": name, "private": private, "messages": messages}

    def test_with_orders_lists_options_in_shared(self):
        builder = ContextBuilder(self._data()).with_orders()
        shared = builder.build_shared()
        assert "Unit lon:" in shared
        assert "0. lon Hold" in shared
        assert "1. lon Move nth" in shared

    def test_with_conversations_labels_senders_by_nation_and_marks_privacy(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [{"body": "hi", "sender": {"is_current_user": False, "nation": {"name": "England"}}}],
            ),
            self._channel(
                2,
                "England, France",
                [{"body": "psst", "sender": {"is_current_user": False, "nation": {"name": "France"}}}],
                private=True,
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_conversations().build_private()
        assert "Channel: Public Press (public)" in private
        assert "Channel: England, France (private)" in private
        assert "England: hi" in private
        assert "France: psst" in private

    def test_with_messages_includes_only_that_channel(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [{"body": "public", "sender": {"is_current_user": False, "nation": {"name": "England"}}}],
            ),
            self._channel(
                2,
                "Private",
                [{"body": "private", "sender": {"is_current_user": False, "nation": {"name": "France"}}}],
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_messages(channel_id=2).build_private()
        assert "Channel: Private" in private
        assert "France: private" in private
        assert "Public Press" not in private

    def test_with_messages_labels_every_message_by_nation(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [
                    {"body": "their turn", "sender": {"is_current_user": False, "nation": {"name": "England"}}},
                    {"body": "my turn", "sender": {"is_current_user": True, "nation": {"name": "Germany"}}},
                ],
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_messages(channel_id=1).build_private()
        assert "England: their turn" in private
        assert "Germany: my turn" in private

    def test_with_messages_falls_back_to_user_without_nation(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [{"body": "anon", "sender": {"is_current_user": False}}],
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_messages(channel_id=1).build_private()
        assert "user: anon" in private

    def test_with_messages_missing_channel_is_noop(self):
        private = ContextBuilder(self._data()).with_messages(channel_id=999).build_private()
        assert private == ""


def _reply_response(should_reply, message=""):
    payload = {"should_reply": should_reply}
    if message:
        payload["message"] = message
    return json.dumps(payload)


def _anthropic_message(text):
    block = Mock(type="text", text=text)
    usage = Mock(
        input_tokens=100,
        output_tokens=20,
        cache_read_input_tokens=50,
        cache_creation_input_tokens=5,
    )
    return Mock(content=[block], model="test-model", usage=usage)


class TestComposeReply:

    def test_returns_reply_when_model_replies(self):
        assert parse_reply(_reply_response(True, "Sure, let's talk.")) == "Sure, let's talk."

    def test_returns_none_when_model_declines(self):
        assert parse_reply(_reply_response(False)) is None

    def test_returns_none_for_empty_message(self):
        assert parse_reply(json.dumps({"should_reply": True, "message": "   "})) is None

    def test_raises_on_unparseable_json(self):
        with pytest.raises(LLMError):
            parse_reply("not json at all")


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

        with patch("bot.api_client.APIClient", return_value=fake_client):
            tasks.plan(user_id=bot_user.id, game_id="some-game")

        assert fake_client.post.call_count == 1

    @pytest.mark.django_db
    def test_plan_submits_all_orders_when_no_limit(self):
        bot_user = get_bot_user()
        fake_client = self._fake_client(max_orders=None)

        with patch("bot.api_client.APIClient", return_value=fake_client):
            tasks.plan(user_id=bot_user.id, game_id="some-game")

        assert fake_client.post.call_count == 3


@pytest.fixture
def bot_game_factory(db, primary_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany):
    def _create():
        game = Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="Bot Game",
            nation_assignment=NationAssignment.ORDERED,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            created_by=primary_user,
        )
        game.members.create(user=primary_user)
        game.members.create(user=get_bot_user())

        with patch.object(
            adjudication_service, "start", return_value=adjudication_data_italy_vs_germany
        ):
            game.start()

        return game

    return _create


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

        with patch("bot.tasks.LLMClient") as mock_llm:
            mock_llm.return_value.complete.return_value = '{"choices": []}'
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        system = mock_llm.return_value.complete.call_args.kwargs["system"]
        assert disposition in system

    @pytest.mark.django_db
    def test_plan_records_success_call(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game = bot_game_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)

        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = _anthropic_message(
                '{"choices": []}'
            )
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        call = LLMCall.objects.get(stage=LLMCallStage.PLAN)
        assert call.status == LLMCallStatus.SUCCESS
        assert call.member == bot_member
        assert call.phase == game.current_phase
        assert call.model == "test-model"
        assert call.output_tokens == 20
        assert call.cache_read_tokens == 50

    @pytest.mark.django_db
    def test_plan_records_error_call_when_llm_raises(
        self, bot_game_factory, in_memory_procrastinate, settings
    ):
        settings.ANTHROPIC_API_KEY = "test-key"
        game = bot_game_factory()
        bot_user = get_bot_user()

        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            tasks.plan(user_id=bot_user.id, game_id=game.id)

        call = LLMCall.objects.get(stage=LLMCallStage.PLAN)
        assert call.status == LLMCallStatus.ERROR
        assert call.error_message
        assert call.input_tokens == 0

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
        assert utils.bot_request_host() == "example.com"

    def test_strips_leading_dot(self, settings):
        settings.ALLOWED_HOSTS = [".railway.app"]
        assert utils.bot_request_host() == "railway.app"

    def test_falls_back_to_testserver_for_wildcard(self, settings):
        settings.ALLOWED_HOSTS = ["*"]
        assert utils.bot_request_host() == "testserver"


class TestBotIdentificationByProfile:

    @pytest.mark.django_db
    def test_get_bot_user_ignores_email(self):
        bot_user = get_bot_user()
        bot_user.email = "not-the-magic-email@example.com"
        bot_user.save()

        assert get_bot_user() == bot_user

    @pytest.mark.django_db
    def test_bot_user_ids_for_phase_ignores_email(self, phase_factory, classical_england_nation):
        bot_user = get_bot_user()
        bot_user.email = "not-the-magic-email@example.com"
        bot_user.save()
        phase = phase_factory(
            phase_states_config=[{"nation": classical_england_nation, "user": bot_user}]
        )

        assert decorators._bot_user_ids_for_phase(phase.id) == {bot_user.id}


class TestBotRoster:

    @pytest.mark.django_db
    def test_roster_is_seeded(self):
        roster = BotProfile.objects.exclude(user=get_bot_user())
        assert roster.count() == 12
        assert all(profile.disposition and profile.voice for profile in roster)

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


def _bot_plan_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "bot.plan"]


def _bot_finalize_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "bot.finalize"]


class TestPlanTrigger:

    @pytest.mark.django_db
    def test_first_phase_activation_defers_plan(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        bot_member = game.members.get(user=get_bot_user())

        jobs = _bot_plan_jobs(in_memory_procrastinate)
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

        assert len(_bot_plan_jobs(in_memory_procrastinate)) == 1

    @pytest.mark.django_db
    def test_non_bot_game_does_not_defer_plan(self, active_game_factory, in_memory_procrastinate):
        active_game_factory()
        assert len(_bot_plan_jobs(in_memory_procrastinate)) == 0


class TestFinalizeTrigger:

    @pytest.mark.django_db
    def test_human_confirm_defers_finalize(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        bot_member = game.members.get(user=get_bot_user())

        human_client = APIClient()
        human_client.force_authenticate(user=game.created_by)
        response = human_client.put(reverse("game-confirm-phase", args=[game.id]))
        assert response.status_code == status.HTTP_200_OK

        jobs = _bot_finalize_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert jobs[0]["lock"] == f"finalize-{game.current_phase.id}-{bot_member.id}"
        assert jobs[0]["args"] == {"user_id": get_bot_user().id, "game_id": game.id}


@pytest.fixture
def bot_public_channel_factory(bot_game_factory):
    def _create():
        game = bot_game_factory()
        channel = game.channels.create(name="Public Press", private=False)
        for member in game.members.all():
            channel.member_channels.create(member=member)
        return game, channel

    return _create


class TestReplyTask:

    @pytest.mark.django_db
    def test_reply_posts_message_when_model_replies(
        self, bot_public_channel_factory, in_memory_procrastinate
    ):
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")

        with patch("bot.tasks.LLMClient") as mock_llm:
            mock_llm.return_value.complete.return_value = _reply_response(True, "Hello, human!")
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        assert channel.messages.filter(sender=bot_member, body="Hello, human!").exists()

    @pytest.mark.django_db
    def test_reply_posts_nothing_when_model_declines(
        self, bot_public_channel_factory, in_memory_procrastinate
    ):
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")

        with patch("bot.tasks.LLMClient") as mock_llm:
            mock_llm.return_value.complete.return_value = _reply_response(False)
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        assert channel.messages.filter(sender__user=bot_user).count() == 0

    @pytest.mark.django_db
    def test_reply_skips_llm_when_message_cap_reached(
        self, bot_public_channel_factory, in_memory_procrastinate, settings
    ):
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        bot_member = game.members.get(user=bot_user)
        for i in range(settings.BOT_CHANNEL_MESSAGE_CAP):
            ChannelMessage.objects.create(
                channel=channel, sender=bot_member, body=f"msg {i}", phase=game.current_phase
            )

        with patch("bot.tasks.LLMClient") as mock_llm:
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)
            mock_llm.return_value.complete.assert_not_called()

        assert channel.messages.filter(sender=bot_member).count() == settings.BOT_CHANNEL_MESSAGE_CAP

    @pytest.mark.django_db
    def test_reply_injects_persona_into_system_prompt(
        self, bot_public_channel_factory, in_memory_procrastinate
    ):
        game, channel = bot_public_channel_factory()
        bot_user = get_bot_user()
        human_member = game.members.get(user=game.created_by)
        ChannelMessage.objects.create(channel=channel, sender=human_member, body="Hi bot")
        disposition = BotProfile.objects.get(user=bot_user).disposition

        with patch("bot.tasks.LLMClient") as mock_llm:
            mock_llm.return_value.complete.return_value = _reply_response(False)
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        system = mock_llm.return_value.complete.call_args.kwargs["system"]
        assert disposition in system


def _bot_reply_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "bot.reply"]


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

        jobs = _bot_reply_jobs(in_memory_procrastinate)
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

        assert len(_bot_reply_jobs(in_memory_procrastinate)) == 0

    @pytest.mark.django_db
    def test_private_channel_message_does_not_defer_reply(
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

        assert len(_bot_reply_jobs(in_memory_procrastinate)) == 0

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

        assert len(_bot_reply_jobs(in_memory_procrastinate)) == 0


class TestLLMCall:

    @pytest.mark.django_db
    def test_records_call_with_usage_and_text(self, bot_game_factory):
        game = bot_game_factory()
        phase = game.current_phase
        member = game.members.get(user=get_bot_user())

        call = LLMCall.objects.create(
            phase=phase,
            member=member,
            stage=LLMCallStage.PLAN,
            model="claude-haiku",
            system="system prompt",
            user_content="user content",
            response="response text",
            input_tokens=120,
            output_tokens=45,
            cache_read_tokens=80,
            cache_write_tokens=10,
        )

        call.refresh_from_db()
        assert call.status == LLMCallStatus.SUCCESS
        assert call.input_tokens == 120
        assert call.cache_read_tokens == 80
        assert call.response == "response text"
        assert call in phase.llm_calls.all()

    @pytest.mark.django_db
    def test_member_is_optional(self, bot_game_factory):
        game = bot_game_factory()

        call = LLMCall.objects.create(
            phase=game.current_phase,
            stage=LLMCallStage.NEGOTIATE,
            model="claude-haiku",
        )

        call.refresh_from_db()
        assert call.member is None
        assert call.input_tokens == 0
        assert call.system == ""


class TestLLMCallRecorder:

    @pytest.mark.django_db
    def test_skips_write_when_phase_id_missing(self, bot_game_factory):
        game = bot_game_factory()
        bot_user = get_bot_user()
        recorder = LLMCallRecorder(
            game_id=game.id, user_id=bot_user.id, phase_id=None, stage=LLMCallStage.REPLY
        )

        recorder.record_error(
            model="m", system="s", user_content="u", error_message="boom", latency_ms=1
        )

        assert LLMCall.objects.count() == 0


llm_call_list_viewname = "llm-call-list"
llm_call_detail_viewname = "llm-call-detail"


class TestLLMCallListView:

    @pytest.mark.django_db
    def test_lists_calls_for_game_ordered_by_created_at(
        self, authenticated_client, bot_game_factory, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = bot_game_factory()
        phase = game.current_phase
        member = game.members.get(user=get_bot_user())

        later = LLMCall.objects.create(
            phase=phase, member=member, stage=LLMCallStage.REPLY, model="claude-haiku"
        )
        earlier = LLMCall.objects.create(
            phase=phase,
            member=member,
            stage=LLMCallStage.PLAN,
            model="claude-haiku",
            input_tokens=10,
            output_tokens=5,
            latency_ms=120,
        )
        # Force deterministic ordering independent of insertion order.
        LLMCall.objects.filter(pk=earlier.pk).update(created_at="2026-01-01T00:00:00Z")
        LLMCall.objects.filter(pk=later.pk).update(created_at="2026-01-02T00:00:00Z")

        response = authenticated_client.get(
            reverse(llm_call_list_viewname), {"game": game.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert [call["id"] for call in response.data] == [earlier.pk, later.pk]

        summary = response.data[0]
        assert summary["stage"] == LLMCallStage.PLAN
        assert summary["status"] == LLMCallStatus.SUCCESS
        assert summary["game_id"] == game.id
        assert summary["total_tokens"] == 15
        assert summary["latency_ms"] == 120
        assert summary["nation"] is not None
        # Heavy fields are reserved for the detail view.
        assert "user_content" not in summary
        assert "response" not in summary

    @pytest.mark.django_db
    def test_filters_by_game(
        self, authenticated_client, bot_game_factory, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = bot_game_factory()
        other_game = bot_game_factory()
        LLMCall.objects.create(
            phase=game.current_phase, stage=LLMCallStage.PLAN, model="m"
        )
        other_call = LLMCall.objects.create(
            phase=other_game.current_phase, stage=LLMCallStage.PLAN, model="m"
        )

        response = authenticated_client.get(
            reverse(llm_call_list_viewname), {"game": other_game.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert [call["id"] for call in response.data] == [other_call.pk]

    @pytest.mark.django_db
    def test_requires_authentication(self, bot_game_factory, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        response = APIClient().get(reverse(llm_call_list_viewname))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_forbidden_when_not_allowlisted(self, authenticated_client, settings):
        settings.BOT_OPPONENT_ALLOWLIST = []
        response = authenticated_client.get(reverse(llm_call_list_viewname))
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLLMCallDetailView:

    @pytest.mark.django_db
    def test_returns_full_content(
        self, authenticated_client, bot_game_factory, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = bot_game_factory()
        member = game.members.get(user=get_bot_user())
        call = LLMCall.objects.create(
            phase=game.current_phase,
            member=member,
            stage=LLMCallStage.PLAN,
            model="claude-haiku",
            system="system prompt",
            user_content="user content",
            response="response text",
            input_tokens=120,
            output_tokens=45,
            cache_read_tokens=80,
            cache_write_tokens=10,
        )

        response = authenticated_client.get(
            reverse(llm_call_detail_viewname, args=[call.pk])
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["system"] == "system prompt"
        assert response.data["user_content"] == "user content"
        assert response.data["response"] == "response text"
        assert response.data["cache_read_tokens"] == 80
        assert response.data["total_tokens"] == 165

    @pytest.mark.django_db
    def test_forbidden_when_not_allowlisted(
        self, authenticated_client, bot_game_factory, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = bot_game_factory()
        call = LLMCall.objects.create(
            phase=game.current_phase, stage=LLMCallStage.PLAN, model="m"
        )
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = authenticated_client.get(
            reverse(llm_call_detail_viewname, args=[call.pk])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


game_create_viewname = "game-create"
available_bots_viewname = "game-available-bots"
add_bot_viewname = "game-add-bot"


def _create_game_via_api(client, variant_id, **overrides):
    payload = {
        "name": "Bot Seat Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    response = client.post(reverse(game_create_viewname), payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    return Game.objects.get(id=response.data["id"])


def _first_roster_bot_user():
    return (
        BotProfile.objects.exclude(user=get_bot_user())
        .order_by("user__profile__name")
        .first()
        .user
    )


class TestAvailableBots:

    @pytest.mark.django_db
    def test_lists_roster_sorted_by_name(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client.get(reverse(available_bots_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 12
        names = [bot["name"] for bot in response.data]
        assert names == sorted(names)
        assert all(bot["user_id"] for bot in response.data)
        assert get_bot_user().id not in [bot["user_id"] for bot in response.data]

    @pytest.mark.django_db
    def test_excludes_bots_already_in_game(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()
        game.members.create(user=bot_user)

        response = authenticated_client.get(reverse(available_bots_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 11
        assert bot_user.id not in [bot["user_id"] for bot in response.data]

    @pytest.mark.django_db
    def test_non_admin_forbidden(
        self, authenticated_client, authenticated_client_for_secondary_user, classical_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com", "secondary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client_for_secondary_user.get(
            reverse(available_bots_viewname, args=[game.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_not_allowlisted_forbidden(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = authenticated_client.get(reverse(available_bots_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_non_pending_game_forbidden(self, authenticated_client, active_game_created_by_primary_user, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]

        response = authenticated_client.get(
            reverse(available_bots_viewname, args=[active_game_created_by_primary_user.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddBot:

    @pytest.mark.django_db
    def test_admin_adds_roster_bot(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_bot"] is True
        assert response.data["name"] == bot_user.profile.name
        bot_member = game.members.get(user=bot_user)
        public_channel = game.channels.get(private=False)
        assert public_channel.member_channels.filter(member=bot_member).exists()
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING

    @pytest.mark.django_db
    def test_filling_last_seat_starts_game(self, authenticated_client, italy_vs_germany_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, italy_vs_germany_variant.id)
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert game.current_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_game_master_adds_roster_bot(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(
            authenticated_client, classical_variant.id, private=True, game_master=True
        )
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert game.members.filter(user=bot_user).exists()

    @pytest.mark.django_db
    def test_bot_already_in_game_rejected(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()
        game.members.create(user=bot_user)

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_generic_bot_rejected(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": get_bot_user().id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_human_user_rejected(self, authenticated_client, classical_variant, secondary_user, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": secondary_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_non_admin_forbidden(
        self, authenticated_client, authenticated_client_for_secondary_user, classical_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com", "secondary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()

        response = authenticated_client_for_secondary_user.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_not_allowlisted_forbidden(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_non_pending_game_forbidden(self, authenticated_client, active_game_created_by_primary_user, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[active_game_created_by_primary_user.id]),
            {"user_id": bot_user.id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
