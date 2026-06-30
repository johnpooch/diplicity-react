from unittest.mock import MagicMock, Mock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from adjudication import service as adjudication_service
from common.constants import (
    DeadlineMode,
    MovementPhaseDuration,
    NationAssignment,
    OrderType,
)
from channel.models import ChannelMessage
from game.models import Game
from bot import tasks, utils
from bot.actions import ReplyAction, SelectOrderAction
from bot.actions.reply import TOOL_NAME as REPLY_TOOL_NAME
from bot.actions.select_order import TOOL_NAME as SELECT_TOOL_NAME
from bot.data import ChatMessage, OrderOption, OrderOptionCollection
from bot.llm_client import LLMClient, LLMError
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
        assert OrderOption(_option("lon", OrderType.HOLD)).to_selected() == ["lon", OrderType.HOLD]

    def test_move(self):
        assert OrderOption(_option("lon", OrderType.MOVE, target="nth")).to_selected() == [
            "lon",
            OrderType.MOVE,
            "nth",
        ]

    def test_move_with_named_coast(self):
        assert OrderOption(
            _option("mid", OrderType.MOVE, target="spa", named_coast="spa/nc")
        ).to_selected() == ["mid", OrderType.MOVE, "spa", "spa/nc"]

    def test_support(self):
        assert OrderOption(
            _option("lon", OrderType.SUPPORT, aux="wal", target="lvp")
        ).to_selected() == ["lon", OrderType.SUPPORT, "wal", "lvp"]

    def test_build_fleet_named_coast(self):
        assert OrderOption(
            _option("stp", OrderType.BUILD, unit_type="Fleet", named_coast="stp/sc")
        ).to_selected() == ["stp", OrderType.BUILD, "Fleet", "stp/sc"]


class TestFirstLegalSelections:

    def test_picks_first_option_per_source(self):
        options = [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
            _option("edi", OrderType.MOVE, target="nwg"),
            _option("edi", OrderType.HOLD),
        ]
        assert OrderOptionCollection.from_api(options).first_legal_selections() == [
            ["lon", OrderType.HOLD],
            ["edi", OrderType.MOVE, "nwg"],
        ]


def _llm_message(choices):
    block = Mock()
    block.type = "tool_use"
    block.name = SELECT_TOOL_NAME
    block.input = {"choices": choices}
    return Mock(content=[block])


class TestSelectOrders:

    def _options(self):
        return [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
            _option("edi", OrderType.HOLD),
            _option("edi", OrderType.MOVE, target="nwg"),
        ]

    def _run(self, options, key="test-key"):
        return LLMClient(key).run(SelectOrderAction(OrderOptionCollection.from_api(options)))

    def test_returns_llm_choice_per_source(self):
        choices = [
            {"source_id": "lon", "option_index": 1},
            {"source_id": "edi", "option_index": 1},
        ]
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = _llm_message(choices)
            selections = self._run(self._options())

        assert selections == [
            ["lon", OrderType.MOVE, "nth"],
            ["edi", OrderType.MOVE, "nwg"],
        ]

    def test_raises_without_key(self):
        with pytest.raises(LLMError):
            LLMClient("")

    def test_raises_when_client_raises(self):
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            with pytest.raises(LLMError):
                self._run(self._options())

    def test_invalid_or_missing_index_falls_back_per_source(self):
        choices = [{"source_id": "lon", "option_index": 9}]
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = _llm_message(choices)
            selections = self._run(self._options())

        assert selections == [
            ["lon", OrderType.HOLD],
            ["edi", OrderType.HOLD],
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
            return Mock(status_code=200, data=options)

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


def _llm_reply(should_reply, message=""):
    block = Mock()
    block.type = "tool_use"
    block.name = REPLY_TOOL_NAME
    block.input = {"should_reply": should_reply, "message": message}
    return Mock(content=[block])


class TestComposeReply:

    def _messages(self):
        return [
            {
                "sender": {"name": "England", "is_current_user": False},
                "body": "Hi bot, want to ally?",
            },
        ]

    def _run(self, key="test-key"):
        return LLMClient(key).run(ReplyAction(ChatMessage.list_from_api(self._messages())))

    def test_returns_reply_when_model_replies(self):
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = _llm_reply(
                True, "Sure, let's talk."
            )
            assert self._run() == "Sure, let's talk."

    def test_returns_none_when_model_declines(self):
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = _llm_reply(False, "")
            assert self._run() is None

    def test_returns_none_for_empty_message(self):
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = _llm_reply(True, "   ")
            assert self._run() is None

    def test_raises_without_key(self):
        with pytest.raises(LLMError):
            LLMClient("")

    def test_raises_when_client_raises(self):
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            with pytest.raises(LLMError):
                self._run()


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
            mock_llm.return_value.run.return_value = "Hello, human!"
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
            mock_llm.return_value.run.return_value = None
            tasks.reply(user_id=bot_user.id, game_id=game.id, channel_id=channel.id)

        assert channel.messages.filter(sender__user=bot_user).count() == 0


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
