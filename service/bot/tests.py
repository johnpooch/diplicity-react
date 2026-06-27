from unittest.mock import patch

import pytest

from adjudication import service as adjudication_service
from common.constants import DeadlineMode, MovementPhaseDuration, NationAssignment, OrderType, PhaseType
from game.models import Game
from order.utils import flatten_options
from bot.play import _option_to_selected, _select_first_legal_orders, play_bot_turn
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


class _StubPhase:
    def __init__(self, phase_type):
        self.type = phase_type


class _StubPhaseState:
    def __init__(self, phase_type, max_orders=float("inf")):
        self.phase = _StubPhase(phase_type)
        self._max_orders = max_orders

    def max_allowed_adjustment_orders(self):
        return self._max_orders


class TestOptionToSelected:

    def test_hold(self):
        assert _option_to_selected(_option("lon", OrderType.HOLD)) == ["lon", OrderType.HOLD]

    def test_move(self):
        assert _option_to_selected(_option("lon", OrderType.MOVE, target="nth")) == [
            "lon",
            OrderType.MOVE,
            "nth",
        ]

    def test_move_with_named_coast(self):
        assert _option_to_selected(
            _option("mid", OrderType.MOVE, target="spa", named_coast="spa/nc")
        ) == ["mid", OrderType.MOVE, "spa", "spa/nc"]

    def test_support(self):
        assert _option_to_selected(
            _option("lon", OrderType.SUPPORT, aux="wal", target="lvp")
        ) == ["lon", OrderType.SUPPORT, "wal", "lvp"]

    def test_build(self):
        assert _option_to_selected(
            _option("lon", OrderType.BUILD, unit_type="Army")
        ) == ["lon", OrderType.BUILD, "Army"]

    def test_build_fleet_named_coast(self):
        assert _option_to_selected(
            _option("stp", OrderType.BUILD, unit_type="Fleet", named_coast="stp/sc")
        ) == ["stp", OrderType.BUILD, "Fleet", "stp/sc"]


class TestSelectFirstLegalOrders:

    def test_picks_first_option_per_source(self):
        options = [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
            _option("edi", OrderType.MOVE, target="nwg"),
            _option("edi", OrderType.HOLD),
        ]
        result = _select_first_legal_orders(options, _StubPhaseState(PhaseType.MOVEMENT))
        assert result == [["lon", OrderType.HOLD], ["edi", OrderType.MOVE, "nwg"]]

    def test_adjustment_caps_at_max_orders(self):
        options = [
            _option("lon", OrderType.BUILD, unit_type="Army"),
            _option("edi", OrderType.BUILD, unit_type="Fleet"),
            _option("lvp", OrderType.BUILD, unit_type="Army"),
        ]
        result = _select_first_legal_orders(
            options, _StubPhaseState(PhaseType.ADJUSTMENT, max_orders=2)
        )
        assert result == [["lon", OrderType.BUILD, "Army"], ["edi", OrderType.BUILD, "Fleet"]]

    def test_movement_not_capped(self):
        options = [_option(f"p{i}", OrderType.HOLD) for i in range(5)]
        result = _select_first_legal_orders(options, _StubPhaseState(PhaseType.MOVEMENT))
        assert len(result) == 5


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


class TestPlayBotTurn:

    @pytest.mark.django_db
    def test_bot_submits_and_confirms_orders(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        phase = game.current_phase
        bot_phase_state = phase.phase_states.get(member__user=get_bot_user())

        play_bot_turn(phase)

        bot_phase_state.refresh_from_db()
        assert bot_phase_state.orders_confirmed is True

        nation_options = phase.transformed_options[bot_phase_state.member.nation.name]
        assert bot_phase_state.orders.count() == len(nation_options)
        assert all(order.complete for order in bot_phase_state.orders.all())

    @pytest.mark.django_db
    def test_bot_orders_match_first_legal_option(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        phase = game.current_phase
        bot_phase_state = phase.phase_states.get(member__user=get_bot_user())

        play_bot_turn(phase)

        province_lookup = {p.province_id: p for p in phase.variant.provinces.all()}
        nation_options = phase.transformed_options[bot_phase_state.member.nation.name]
        flat = flatten_options(nation_options, province_lookup)
        expected_first = {}
        for option in flat:
            expected_first.setdefault(option["source"]["id"], option["order_type"]["id"])

        for order in bot_phase_state.orders.all():
            assert order.order_type == expected_first[order.source.province_id]

    @pytest.mark.django_db
    def test_play_bot_turn_is_idempotent(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        phase = game.current_phase
        bot_phase_state = phase.phase_states.get(member__user=get_bot_user())

        play_bot_turn(phase)
        order_count = bot_phase_state.orders.count()
        play_bot_turn(phase)

        assert bot_phase_state.orders.count() == order_count


class TestBotTrigger:

    @pytest.mark.django_db
    def test_starting_bot_game_defers_bot_task(self, bot_game_factory, in_memory_procrastinate):
        game = bot_game_factory()
        jobs = [
            j for j in in_memory_procrastinate.jobs.values() if j["task_name"] == "bot.play_phase"
        ]
        assert len(jobs) == 1
        assert jobs[0]["lock"] == f"bot-game-{game.id}"
        assert jobs[0]["args"] == {"phase_id": game.current_phase.id}

    @pytest.mark.django_db
    def test_non_bot_game_does_not_defer_bot_task(
        self, active_game_factory, in_memory_procrastinate
    ):
        active_game_factory()
        jobs = [
            j for j in in_memory_procrastinate.jobs.values() if j["task_name"] == "bot.play_phase"
        ]
        assert len(jobs) == 0
