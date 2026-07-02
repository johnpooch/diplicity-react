import json
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
from bot.models import BotProfile, LLMCall
from bot import decorators, tasks, utils
from bot.constants import LLMCallStage, LLMCallStatus
from bot.context.builder import ContextBuilder
from bot.context.map import (
    build_graph,
    nearest_enemy_units,
    nearest_uncontrolled_supply_centers,
    shortest_distances,
)
from bot.context.orders import first_legal_selections, option_to_selected
from bot.context.parsers import parse_order_selections, parse_reply
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
            LLMClient("")

    def test_raises_when_client_raises(self):
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.side_effect = RuntimeError("boom")
            with pytest.raises(LLMError):
                LLMClient("test-key").complete(system="s", messages=[{"role": "user", "content": "x"}])

    def test_returns_concatenated_text_blocks(self):
        block_one = Mock(type="text", text="Hello, ")
        block_two = Mock(type="text", text="human!")
        with patch("bot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = Mock(
                content=[block_one, block_two]
            )
            result = LLMClient("test-key").complete(
                system="s", messages=[{"role": "user", "content": "x"}]
            )
        assert result == "Hello, human!"


def _map_province(province_id, type="coastal", supply_center=False, parent_id=None, adjacencies=None):
    return {
        "id": province_id,
        "name": province_id,
        "type": type,
        "supply_center": supply_center,
        "parent_id": parent_id,
        "adjacencies": adjacencies or [],
    }


def _map_unit(unit_type, nation, province_id, dislodged=False):
    return {
        "type": unit_type,
        "nation": {"nation_id": nation.lower(), "name": nation},
        "province": {"id": province_id, "name": province_id},
        "dislodged": dislodged,
    }


class TestMapGraph:

    def _provinces(self):
        return [
            _map_province("a", type="land", supply_center=True, adjacencies=[{"to": "b", "pass": "army"}]),
            _map_province(
                "b",
                adjacencies=[
                    {"to": "a", "pass": "army"},
                    {"to": "c", "pass": "both"},
                    {"to": "s", "pass": "fleet"},
                ],
            ),
            _map_province(
                "c",
                supply_center=True,
                adjacencies=[{"to": "b", "pass": "both"}, {"to": "s", "pass": "fleet"}],
            ),
            _map_province(
                "s",
                type="sea",
                adjacencies=[
                    {"to": "b", "pass": "fleet"},
                    {"to": "c", "pass": "fleet"},
                    {"to": "c/nc", "pass": "fleet"},
                ],
            ),
            _map_province("c/nc", type="named_coast", parent_id="c", adjacencies=[{"to": "s", "pass": "fleet"}]),
        ]

    def _data(self, units, supply_centers=None):
        return {
            "phase": {"units": units, "supply_centers": supply_centers or []},
            "variant": {"provinces": self._provinces()},
        }

    def test_build_graph_typed_edges_collapse_named_coasts(self):
        graph = build_graph(self._provinces())
        assert graph["edges"]["a"] == {"army": ["b"], "fleet": []}
        assert graph["edges"]["b"] == {"army": ["a", "c"], "fleet": ["c", "s"]}
        assert "c/nc" not in graph["edges"]
        assert graph["canonical"]["c/nc"] == "c"
        assert graph["edges"]["s"]["fleet"] == ["b", "c"]

    def test_shortest_distances_respect_pass_type(self):
        graph = build_graph(self._provinces())
        assert shortest_distances(graph, "a", "army") == {"a": 0, "b": 1, "c": 2}
        fleet_from_sea = shortest_distances(graph, "s", "fleet")
        assert fleet_from_sea == {"s": 0, "b": 1, "c": 1}

    def test_nearest_enemy_units_ties_break_by_province_id(self):
        graph = build_graph(self._provinces())
        unit = _map_unit("Army", "England", "b")
        enemies = [
            _map_unit("Army", "France", "c"),
            _map_unit("Army", "France", "a"),
            _map_unit("Fleet", "France", "s", dislodged=True),
        ]
        nearest = nearest_enemy_units(self._data([unit] + enemies), graph, unit)
        assert [(e["province"]["id"], d) for e, d in nearest] == [("a", 1), ("c", 1)]

    def test_nearest_enemy_units_caps_at_n(self):
        graph = build_graph(self._provinces())
        unit = _map_unit("Army", "England", "b")
        enemies = [_map_unit("Army", "France", "a"), _map_unit("Army", "France", "c")]
        nearest = nearest_enemy_units(self._data([unit] + enemies), graph, unit, n=1)
        assert len(nearest) == 1

    def test_nearest_uncontrolled_scs_include_dist_zero_and_filter_owned(self):
        graph = build_graph(self._provinces())
        unit = _map_unit("Army", "England", "c")
        supply_centers = [
            {
                "province": {"id": "a", "name": "a"},
                "nation": {"nation_id": "france", "name": "France"},
            }
        ]
        nearest = nearest_uncontrolled_supply_centers(
            self._data([unit], supply_centers), graph, unit
        )
        assert nearest == [("c", None, 0), ("a", "France", 2)]

        french_unit = _map_unit("Army", "France", "c")
        nearest = nearest_uncontrolled_supply_centers(
            self._data([french_unit], supply_centers), graph, french_unit
        )
        assert nearest == [("c", None, 0)]

    def test_missing_adjacencies_degrade_gracefully(self):
        provinces = [
            _map_province("a", supply_center=True),
            _map_province("b"),
        ]
        graph = build_graph(provinces)
        assert shortest_distances(graph, "b", "army") == {"b": 0}
        unit = _map_unit("Army", "England", "b")
        data = {
            "phase": {"units": [unit, _map_unit("Army", "France", "a")], "supply_centers": []},
            "variant": {"provinces": provinces},
        }
        assert nearest_enemy_units(data, graph, unit) == []
        assert nearest_uncontrolled_supply_centers(data, graph, unit) == []
        assert build_graph([]) == {"edges": {}, "canonical": {}}


class TestContextBuilder:

    def _data(self, channels=None, phase=None, variant=None):
        return {
            "orders": [
                _option("lon", OrderType.HOLD),
                _option("lon", OrderType.MOVE, target="nth"),
            ],
            "phase_states": [{"max_orders": 3, "member": {"nation": "England"}}],
            "game": {"phase_confirmed": False},
            "phase": phase if phase is not None else {},
            "channels": channels or [],
            "variant": variant or {},
        }

    def _variant(self):
        return {
            "id": "test",
            "provinces": [
                _map_province(
                    "lon",
                    supply_center=True,
                    adjacencies=[
                        {"to": "nth", "pass": "fleet"},
                        {"to": "wal", "pass": "army"},
                        {"to": "edi", "pass": "army"},
                        {"to": "par", "pass": "army"},
                    ],
                ),
                _map_province(
                    "nth",
                    type="sea",
                    adjacencies=[{"to": "lon", "pass": "fleet"}, {"to": "edi", "pass": "fleet"}],
                ),
                _map_province(
                    "edi",
                    supply_center=True,
                    adjacencies=[{"to": "lon", "pass": "army"}, {"to": "nth", "pass": "fleet"}],
                ),
                _map_province("wal", adjacencies=[{"to": "lon", "pass": "army"}]),
                _map_province(
                    "par",
                    type="land",
                    supply_center=True,
                    adjacencies=[{"to": "lon", "pass": "army"}],
                ),
            ],
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
        assert "England: 2 (A lon, F nth (dislodged))" in shared
        assert "France: 1 (A par)" in shared
        assert "England: 2 (edi, lon)" in shared
        assert "France: 1 (par)" in shared

    def test_with_game_state_empty_phase_is_noop(self):
        assert ContextBuilder(self._data()).with_game_state().build_shared() == ""

    def test_with_game_state_retreat_phase_lists_dislodged_units(self):
        phase = self._phase()
        phase["type"] = "Retreat"
        shared = ContextBuilder(self._data(phase=phase)).with_game_state().build_shared()
        assert "Dislodged units: F nth (England)" in shared

    def test_with_game_state_adjustment_phase_frames_per_nation(self):
        def nation(name):
            return {"nation_id": name.lower(), "name": name}

        def province(province_id):
            return {"id": province_id, "name": province_id}

        phase = {
            "name": "Winter 1901, Adjustment",
            "type": "Adjustment",
            "units": [
                {"type": "Army", "nation": nation("England"), "province": province("lon"), "dislodged": False},
                {"type": "Army", "nation": nation("France"), "province": province("par"), "dislodged": False},
                {"type": "Fleet", "nation": nation("France"), "province": province("bre"), "dislodged": False},
                {"type": "Army", "nation": nation("Germany"), "province": province("mun"), "dislodged": False},
            ],
            "supply_centers": [
                {"province": province("lon"), "nation": nation("England")},
                {"province": province("edi"), "nation": nation("England")},
                {"province": province("par"), "nation": nation("France")},
                {"province": province("mun"), "nation": nation("Germany")},
            ],
        }
        shared = ContextBuilder(self._data(phase=phase)).with_game_state().build_shared()
        assert "Adjustments:" in shared
        assert "England: 1 build available" in shared
        assert "France: 1 disband required" in shared
        assert "Germany: no change" in shared

    def test_with_tactical_annotations_renders_unit_blocks(self):
        shared = (
            ContextBuilder(self._data(phase=self._phase(), variant=self._variant()))
            .with_tactical_annotations()
            .build_shared()
        )
        assert "Tactical annotations:" in shared
        assert "Unit A lon (England):" in shared
        assert (
            "  Adjacent: edi (SC: England, empty), par (SC: France, occupied A par France), wal (no SC, empty)"
            in shared
        )
        assert "  Nearest enemy units: A par (France, dist 1)" in shared
        assert "  Nearest uncontrolled supply centers: par (France, dist 1)" in shared
        assert "Unit F nth (England, dislodged):" in shared
        assert "Nearest enemy units: none" in shared

    def test_with_tactical_annotations_without_variant_is_noop(self):
        shared = (
            ContextBuilder(self._data(phase=self._phase()))
            .with_tactical_annotations()
            .build_shared()
        )
        assert shared == ""

    def test_shared_block_is_byte_identical_across_builds(self):
        def build():
            return (
                ContextBuilder(self._data(phase=self._phase(), variant=self._variant()))
                .with_game_state()
                .with_tactical_annotations()
                .build_shared()
            )

        assert build() == build()

    def test_with_identity_names_nation_in_private(self):
        builder = ContextBuilder(self._data()).with_identity()
        assert "You are playing England." in builder.build_private()
        assert builder.build_shared() == ""

    def _channel(self, channel_id, name, messages):
        return {"id": channel_id, "name": name, "private": False, "messages": messages}

    def test_with_orders_lists_options_in_private(self):
        builder = ContextBuilder(self._data()).with_orders()
        private = builder.build_private()
        assert "Unit lon:" in private
        assert "0. lon Hold" in private
        assert "1. lon Move nth" in private
        assert "Legal orders:" not in builder.build_shared()

    def test_with_phase_state_is_private(self):
        builder = ContextBuilder(self._data()).with_phase_state()
        assert "Orders to submit this phase: 3" in builder.build_private()
        assert builder.build_shared() == ""

    def test_with_conversations_includes_all_channels(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [{"body": "hi", "sender": {"name": "England", "is_current_user": False}}],
            ),
            self._channel(
                2,
                "Private",
                [{"body": "psst", "sender": {"name": "France", "is_current_user": False}}],
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_conversations().build_private()
        assert "Channel: Public Press" in private
        assert "Channel: Private" in private
        assert "user: hi" in private
        assert "user: psst" in private

    def test_with_messages_includes_only_that_channel(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [{"body": "public", "sender": {"name": "England", "is_current_user": False}}],
            ),
            self._channel(
                2,
                "Private",
                [{"body": "private", "sender": {"name": "France", "is_current_user": False}}],
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_messages(channel_id=2).build_private()
        assert "Channel: Private" in private
        assert "private" in private
        assert "Public Press" not in private

    def test_with_messages_maps_own_messages_to_assistant(self):
        channels = [
            self._channel(
                1,
                "Public Press",
                [
                    {"body": "their turn", "sender": {"name": "England", "is_current_user": False}},
                    {"body": "my turn", "sender": {"name": "Bot", "is_current_user": True}},
                ],
            ),
        ]
        private = ContextBuilder(self._data(channels)).with_messages(channel_id=1).build_private()
        assert "user: their turn" in private
        assert "assistant: my turn" in private

    def test_with_messages_missing_channel_is_noop(self):
        private = ContextBuilder(self._data()).with_messages(channel_id=999).build_private()
        assert private == ""


def _reply_response(should_reply, message=""):
    payload = {"should_reply": should_reply}
    if message:
        payload["message"] = message
    return json.dumps(payload)


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
