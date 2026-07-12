import json

import pytest

from common.constants import OrderType

from harness.blocks import (
    ChannelMessagesBlock,
    GameStateBlock,
    IdentityBlock,
    LegalOrdersBlock,
    PhaseStateBlock,
    render_persona,
)
from harness.exceptions import ParseError
from harness.orders import option_to_selected
from harness.prompt import build_prompt
from harness.tasks import ReplyTask, SelectOrdersTask
from harness.types import Persona, TaskContext


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


def _data(channels=None, phase=None, variant=None, orders=None, phase_states=None):
    return {
        "orders": orders
        if orders is not None
        else [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
        ],
        "phase_states": phase_states
        if phase_states is not None
        else [{"max_orders": 3, "member": {"nation": "England"}}],
        "game": {"phase_confirmed": False},
        "phase": phase if phase is not None else {},
        "channels": channels or [],
        "variant": variant or {},
    }


def _nation(name):
    return {"nation_id": name.lower(), "name": name}


def _province(province_id):
    return {"id": province_id, "name": province_id}


def _phase():
    return {
        "name": "Spring 1901, Movement",
        "type": "Movement",
        "units": [
            {"type": "Army", "nation": _nation("England"), "province": _province("lon"), "dislodged": False},
            {"type": "Fleet", "nation": _nation("England"), "province": _province("nth"), "dislodged": True},
            {"type": "Army", "nation": _nation("France"), "province": _province("par"), "dislodged": False},
        ],
        "supply_centers": [
            {"province": _province("lon"), "nation": _nation("England")},
            {"province": _province("edi"), "nation": _nation("England")},
            {"province": _province("par"), "nation": _nation("France")},
        ],
    }


def _channel(channel_id, name, messages, private=False):
    return {"id": channel_id, "name": name, "private": private, "messages": messages}


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


class TestGameStateBlock:

    def test_groups_units_and_centers_by_nation(self):
        rendered = GameStateBlock().render(_data(phase=_phase()), TaskContext())
        assert "Current phase: Spring 1901, Movement" in rendered
        assert "England: 2 (A lon, F nth (dislodged))" in rendered
        assert "France: 1 (A par)" in rendered
        assert "England: 2 (edi, lon)" in rendered
        assert "France: 1 (par)" in rendered

    def test_empty_phase_renders_nothing(self):
        assert GameStateBlock().render(_data(), TaskContext()) is None

    def test_retreat_phase_lists_dislodged_units(self):
        phase = _phase()
        phase["type"] = "Retreat"
        rendered = GameStateBlock().render(_data(phase=phase), TaskContext())
        assert "Dislodged units: F nth (England)" in rendered

    def test_adjustment_phase_frames_per_nation(self):
        phase = {
            "name": "Winter 1901, Adjustment",
            "type": "Adjustment",
            "units": [
                {"type": "Army", "nation": _nation("England"), "province": _province("lon"), "dislodged": False},
                {"type": "Army", "nation": _nation("France"), "province": _province("par"), "dislodged": False},
                {"type": "Fleet", "nation": _nation("France"), "province": _province("bre"), "dislodged": False},
                {"type": "Army", "nation": _nation("Germany"), "province": _province("mun"), "dislodged": False},
            ],
            "supply_centers": [
                {"province": _province("lon"), "nation": _nation("England")},
                {"province": _province("edi"), "nation": _nation("England")},
                {"province": _province("par"), "nation": _nation("France")},
                {"province": _province("mun"), "nation": _nation("Germany")},
            ],
        }
        rendered = GameStateBlock().render(_data(phase=phase), TaskContext())
        assert "Adjustments:" in rendered
        assert "England: 1 build available" in rendered
        assert "France: 1 disband required" in rendered
        assert "Germany: no change" in rendered


class TestIdentityBlock:

    def test_names_nation(self):
        assert IdentityBlock().render(_data(), TaskContext()) == "You are playing England."

    def test_renders_nothing_without_phase_states(self):
        assert IdentityBlock().render(_data(phase_states=[]), TaskContext()) is None


class TestLegalOrdersBlock:

    def test_lists_options_by_source(self):
        rendered = LegalOrdersBlock().render(_data(), TaskContext())
        assert "Legal orders:" in rendered
        assert "Unit lon:" in rendered
        assert "0. lon Hold" in rendered
        assert "1. lon Move nth" in rendered


class TestPhaseStateBlock:

    def test_states_max_orders(self):
        rendered = PhaseStateBlock().render(_data(), TaskContext())
        assert rendered == "Orders to submit this phase: 3"

    def test_renders_nothing_without_max_orders(self):
        data = _data(phase_states=[{"member": {"nation": "England"}}])
        assert PhaseStateBlock().render(data, TaskContext()) is None


class TestChannelMessagesBlock:

    def test_includes_only_that_channel(self):
        channels = [
            _channel(
                1,
                "Public Press",
                [{"body": "public", "sender": {"is_current_user": False, "nation": {"name": "England"}}}],
            ),
            _channel(
                2,
                "Private",
                [{"body": "private", "sender": {"is_current_user": False, "nation": {"name": "France"}}}],
            ),
        ]
        rendered = ChannelMessagesBlock().render(_data(channels), TaskContext(channel_id=2))
        assert "Channel: Private" in rendered
        assert "France: private" in rendered
        assert "Public Press" not in rendered

    def test_labels_every_message_by_nation_and_marks_privacy(self):
        channels = [
            _channel(
                1,
                "England, France",
                [
                    {"body": "their turn", "sender": {"is_current_user": False, "nation": {"name": "England"}}},
                    {"body": "my turn", "sender": {"is_current_user": True, "nation": {"name": "Germany"}}},
                ],
                private=True,
            ),
        ]
        rendered = ChannelMessagesBlock().render(_data(channels), TaskContext(channel_id=1))
        assert "Channel: England, France (private)" in rendered
        assert "England: their turn" in rendered
        assert "Germany: my turn" in rendered

    def test_falls_back_to_user_without_nation(self):
        channels = [
            _channel(1, "Public Press", [{"body": "anon", "sender": {"is_current_user": False}}]),
        ]
        rendered = ChannelMessagesBlock().render(_data(channels), TaskContext(channel_id=1))
        assert "user: anon" in rendered

    def test_missing_channel_renders_nothing(self):
        assert ChannelMessagesBlock().render(_data(), TaskContext(channel_id=999)) is None


class TestBuildPrompt:

    def test_assembles_blocks_and_instruction(self):
        prompt = build_prompt(SelectOrdersTask, _data(phase=_phase()), TaskContext())
        assert prompt.system == SelectOrdersTask.system_prompt
        assert "Current phase: Spring 1901, Movement" in prompt.user_content
        assert "You are playing England." in prompt.user_content
        assert "Legal orders:" in prompt.user_content
        assert "Orders to submit this phase: 3" in prompt.user_content
        assert prompt.user_content.endswith(SelectOrdersTask.instruction)
        assert prompt.output_schema == SelectOrdersTask.output_schema
        assert prompt.max_tokens is None

    def test_skips_empty_blocks(self):
        prompt = build_prompt(ReplyTask, _data(), TaskContext(channel_id=999))
        assert prompt.user_content == "You are playing England.\n\n" + ReplyTask.instruction

    def test_appends_persona_to_system(self):
        persona = Persona(disposition="ruthless", voice="clipped")
        prompt = build_prompt(SelectOrdersTask, _data(), TaskContext(persona=persona))
        assert prompt.system.startswith(SelectOrdersTask.system_prompt)
        assert render_persona(persona) in prompt.system
        assert "Disposition: ruthless" in prompt.system
        assert "Voice: clipped" in prompt.system

    def test_is_deterministic_across_builds(self):
        def build():
            return build_prompt(SelectOrdersTask, _data(phase=_phase()), TaskContext())

        assert build() == build()


class TestSelectOrdersParse:

    def _options(self):
        return [
            _option("lon", OrderType.HOLD),
            _option("lon", OrderType.MOVE, target="nth"),
            _option("edi", OrderType.HOLD),
            _option("edi", OrderType.MOVE, target="nwg"),
        ]

    def _context(self):
        return _data(orders=self._options())

    def test_returns_choice_per_source(self):
        response = json.dumps(
            {
                "choices": [
                    {"source_id": "lon", "option_index": 1},
                    {"source_id": "edi", "option_index": 1},
                ]
            }
        )
        assert SelectOrdersTask.parse(response, context=self._context()) == [
            ["lon", OrderType.MOVE, "nth"],
            ["edi", OrderType.MOVE, "nwg"],
        ]

    def test_parses_json_wrapped_in_markdown_fence(self):
        response = (
            "```json\n"
            + json.dumps({"choices": [{"source_id": "lon", "option_index": 1}]})
            + "\n```"
        )
        assert SelectOrdersTask.parse(response, context=self._context()) == [
            ["lon", OrderType.MOVE, "nth"],
        ]

    def test_invalid_or_missing_index_skips_that_source(self):
        response = json.dumps(
            {
                "choices": [
                    {"source_id": "lon", "option_index": 9},
                    {"source_id": "edi", "option_index": 0},
                ]
            }
        )
        assert SelectOrdersTask.parse(response, context=self._context()) == [
            ["edi", OrderType.HOLD],
        ]

    def test_ignores_reasoning_field(self):
        response = json.dumps(
            {
                "reasoning": "Hold London and move Edinburgh north.",
                "choices": [
                    {"source_id": "lon", "option_index": 0},
                    {"source_id": "edi", "option_index": 1},
                ],
            }
        )
        assert SelectOrdersTask.parse(response, context=self._context()) == [
            ["lon", OrderType.HOLD],
            ["edi", OrderType.MOVE, "nwg"],
        ]

    def test_raises_on_unparseable_json(self):
        with pytest.raises(ParseError):
            SelectOrdersTask.parse("not json at all", context=self._context())

    def test_raises_on_missing_choices(self):
        with pytest.raises(ParseError):
            SelectOrdersTask.parse(json.dumps({"reasoning": "hm"}), context=self._context())

    def test_raises_when_no_valid_selection_produced(self):
        response = json.dumps({"choices": [{"source_id": "lon", "option_index": 9}]})
        with pytest.raises(ParseError):
            SelectOrdersTask.parse(response, context=self._context())

    def test_empty_choices_without_options_returns_empty(self):
        response = json.dumps({"choices": []})
        assert SelectOrdersTask.parse(response, context=_data(orders=[])) == []


class TestReplyParse:

    def test_returns_message(self):
        response = json.dumps({"reasoning": "answer them", "message": "Sure, let's talk."})
        assert ReplyTask.parse(response, context=_data()) == "Sure, let's talk."

    def test_returns_none_for_empty_message(self):
        assert ReplyTask.parse(json.dumps({"message": "   "}), context=_data()) is None

    def test_raises_on_unparseable_json(self):
        with pytest.raises(ParseError):
            ReplyTask.parse("not json at all", context=_data())
