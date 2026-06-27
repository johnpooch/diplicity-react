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
from game.models import Game
from bot import tasks, utils
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
        assert utils.option_to_selected(_option("lon", OrderType.HOLD)) == ["lon", OrderType.HOLD]

    def test_move(self):
        assert utils.option_to_selected(_option("lon", OrderType.MOVE, target="nth")) == [
            "lon",
            OrderType.MOVE,
            "nth",
        ]

    def test_move_with_named_coast(self):
        assert utils.option_to_selected(
            _option("mid", OrderType.MOVE, target="spa", named_coast="spa/nc")
        ) == ["mid", OrderType.MOVE, "spa", "spa/nc"]

    def test_support(self):
        assert utils.option_to_selected(
            _option("lon", OrderType.SUPPORT, aux="wal", target="lvp")
        ) == ["lon", OrderType.SUPPORT, "wal", "lvp"]

    def test_build_fleet_named_coast(self):
        assert utils.option_to_selected(
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
        assert utils.first_legal_selections(options) == [
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
            return Mock(status_code=200, data=options)

        client = MagicMock()
        client.get.side_effect = fake_get
        client.post.return_value = Mock(status_code=201)
        return client

    @pytest.mark.django_db
    def test_plan_caps_orders_at_max_orders(self):
        bot_user = get_bot_user()
        fake_client = self._fake_client(max_orders=1)

        with patch("bot.tasks.APIClient", return_value=fake_client):
            tasks.plan(user_id=bot_user.id, game_id="some-game")

        assert fake_client.post.call_count == 1

    @pytest.mark.django_db
    def test_plan_submits_all_orders_when_no_limit(self):
        bot_user = get_bot_user()
        fake_client = self._fake_client(max_orders=None)

        with patch("bot.tasks.APIClient", return_value=fake_client):
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
