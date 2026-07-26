import json

import pytest
from inspect_ai.scorer import CORRECT, INCORRECT, Target

from common.constants import OrderType

from harness_v2.exceptions import ContextError, ParsingError
from harness_v2.tasks.reply.parser import parse_completion as parse_reply
from harness_v2.tasks.reply.user_prompt import user_prompt as reply_user_prompt
from harness_v2.tasks.select_orders.parser import parse_completion
from harness_v2.tasks.select_orders.scorers import (
    convoy_coherence,
    coverage,
    deduplication,
    legality,
    support_coherence,
)


def _option(source, order_type, target=None, aux=None, unit_type=None, named_coast=None):
    return {
        "source": source,
        "order_type": order_type,
        "target": target,
        "aux": aux,
        "unit_type": unit_type,
        "named_coast": named_coast,
    }


def _context(options, max_orders=None):
    return {"order_options": options, "max_orders": max_orders, "provinces": []}


def _completion(choices):
    return json.dumps(
        {
            "reasoning": "because",
            "choices": [{"source_id": source, "option_index": index} for source, index in choices],
        }
    )


class _FakeOutput:
    def __init__(self, completion):
        self.completion = completion


class _FakeState:
    def __init__(self, completion, context):
        self.output = _FakeOutput(completion)
        self.metadata = {"context": context}


def _state(completion, options, max_orders=None):
    return _FakeState(completion, _context(options, max_orders))


def _run(scorer_factory, state):
    score_fn = scorer_factory()
    coro = score_fn(state, Target(""))
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    raise AssertionError("scorer awaited something; expected it to be synchronous")


STRUCTURE_OPTIONS = [
    _option("lon", OrderType.HOLD),
    _option("lon", OrderType.MOVE, target="eng"),
    _option("par", OrderType.HOLD),
    _option("par", OrderType.MOVE, target="bur"),
    _option("ber", OrderType.HOLD),
    _option("ber", OrderType.MOVE, target="kie"),
]


class TestParseCompletion:

    def test_valid_choices_return_selected_options(self):
        completion = _completion([("lon", 0), ("par", 1), ("ber", 0)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [
            _option("lon", OrderType.HOLD),
            _option("par", OrderType.MOVE, target="bur"),
            _option("ber", OrderType.HOLD),
        ]

    def test_fenced_completion_parses(self):
        completion = f"```json\n{_completion([('lon', 0)])}\n```"
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("lon", OrderType.HOLD)]

    def test_invalid_json_raises(self):
        with pytest.raises(ParsingError):
            parse_completion("not json at all", _context(STRUCTURE_OPTIONS))

    def test_non_object_json_raises(self):
        with pytest.raises(ParsingError):
            parse_completion("[]", _context(STRUCTURE_OPTIONS))

    def test_missing_choices_raises(self):
        with pytest.raises(ParsingError):
            parse_completion(json.dumps({"reasoning": "no choices"}), _context(STRUCTURE_OPTIONS))

    def test_out_of_range_index_is_skipped(self):
        completion = _completion([("lon", 99), ("par", 0)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("par", OrderType.HOLD)]

    def test_negative_index_is_skipped(self):
        completion = _completion([("lon", -1)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == []

    def test_non_integer_index_is_skipped(self):
        completion = _completion([("lon", "0")])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == []

    def test_boolean_index_is_skipped(self):
        completion = _completion([("lon", True)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == []

    def test_unknown_source_is_ignored(self):
        completion = _completion([("mos", 0), ("lon", 0)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("lon", OrderType.HOLD)]

    def test_last_choice_per_source_wins(self):
        completion = _completion([("lon", 0), ("lon", 1)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [
            _option("lon", OrderType.MOVE, target="eng")
        ]


class TestLegality:

    def test_valid_selection_is_correct(self):
        state = _state(_completion([("lon", 0), ("par", 0), ("ber", 0)]), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == CORRECT

    def test_invalid_json_is_incorrect(self):
        state = _state("not json at all", STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT


class TestDeduplication:

    def test_distinct_provinces_are_correct(self):
        state = _state(_completion([("lon", 0), ("par", 0), ("ber", 0)]), STRUCTURE_OPTIONS)
        assert _run(deduplication, state).value == CORRECT

    def test_repeated_choices_for_one_province_collapse_to_one(self):
        state = _state(_completion([("lon", 0), ("lon", 1), ("par", 0), ("ber", 0)]), STRUCTURE_OPTIONS)
        assert _run(deduplication, state).value == CORRECT
        assert _run(coverage, state).value == CORRECT


class TestCoverage:

    def test_all_provinces_covered_is_correct(self):
        state = _state(_completion([("lon", 0), ("par", 0), ("ber", 0)]), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == CORRECT

    def test_missing_province_is_incorrect(self):
        state = _state(_completion([("lon", 0), ("par", 0)]), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == INCORRECT

    def test_out_of_range_pick_does_not_count_as_coverage(self):
        state = _state(_completion([("lon", 0), ("par", 0), ("ber", 99)]), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == INCORRECT

    def test_max_orders_exact_count_is_correct(self):
        state = _state(_completion([("lon", 0)]), STRUCTURE_OPTIONS, max_orders=1)
        assert _run(coverage, state).value == CORRECT

    def test_max_orders_over_selection_is_incorrect(self):
        state = _state(_completion([("lon", 0), ("par", 0)]), STRUCTURE_OPTIONS, max_orders=1)
        assert _run(coverage, state).value == INCORRECT

    def test_max_orders_no_selection_is_incorrect(self):
        state = _state(_completion([]), STRUCTURE_OPTIONS, max_orders=1)
        assert _run(coverage, state).value == INCORRECT


SUPPORT_OPTIONS = [
    _option("lon", OrderType.MOVE, target="lvp"),
    _option("lon", OrderType.HOLD),
    _option("wal", OrderType.SUPPORT, aux="lon", target="lvp"),
    _option("wal", OrderType.SUPPORT, aux="lon", target="lon"),
    _option("wal", OrderType.HOLD),
]


class TestSupportCoherence:

    def test_supported_move_present_is_coherent(self):
        state = _state(_completion([("lon", 0), ("wal", 0)]), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == CORRECT

    def test_supported_move_absent_dangles(self):
        state = _state(_completion([("lon", 1), ("wal", 0)]), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == INCORRECT

    def test_supported_hold_present_is_coherent(self):
        state = _state(_completion([("lon", 1), ("wal", 1)]), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == CORRECT

    def test_supported_unit_moves_away_dangles_hold(self):
        state = _state(_completion([("lon", 0), ("wal", 1)]), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == INCORRECT

    def test_support_with_aux_unselected_dangles(self):
        state = _state(_completion([("wal", 1)]), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == INCORRECT

    def test_no_support_selected_is_coherent(self):
        state = _state(_completion([("lon", 1), ("wal", 2)]), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == CORRECT


CONVOY_OPTIONS = [
    _option("eng", OrderType.CONVOY, aux="lon", target="bre"),
    _option("eng", OrderType.HOLD),
    _option("lon", OrderType.MOVE, target="bre"),
    _option("lon", OrderType.HOLD),
]


class TestConvoyCoherence:

    def test_convoyed_move_present_is_coherent(self):
        state = _state(_completion([("eng", 0), ("lon", 0)]), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == CORRECT

    def test_convoyed_army_holds_dangles(self):
        state = _state(_completion([("eng", 0), ("lon", 1)]), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == INCORRECT

    def test_convoyed_army_absent_dangles(self):
        state = _state(_completion([("eng", 0)]), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == INCORRECT

    def test_no_convoy_selected_is_coherent(self):
        state = _state(_completion([("eng", 1), ("lon", 0)]), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == CORRECT


class TestParseReply:

    def test_message_is_returned_stripped(self):
        assert parse_reply(json.dumps({"reasoning": "r", "message": "  Hello.  "})) == "Hello."

    def test_empty_message_returns_none(self):
        assert parse_reply(json.dumps({"reasoning": "r", "message": "   "})) is None

    def test_missing_message_returns_none(self):
        assert parse_reply(json.dumps({"reasoning": "r"})) is None

    def test_invalid_json_raises(self):
        with pytest.raises(ParsingError):
            parse_reply("not json at all")


class TestReplyUserPrompt:

    def _reply_context(self):
        return {
            "members": [{"name": "Bot", "nation": "England", "is_current_user": True}],
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "max_orders": None,
            "provinces": [],
            "units": [{"type": "Army", "nation": "England", "province": "lon", "dislodged": False}],
            "supply_centers": [{"nation": "England", "province": "lon"}],
            "order_options": [],
            "channels": [
                {
                    "id": 7,
                    "name": "Public Press",
                    "private": False,
                    "messages": [{"sender": "France", "body": "Hello England"}],
                }
            ],
        }

    def test_prompt_includes_identity_board_and_conversation(self):
        prompt = reply_user_prompt(self._reply_context(), 7)
        assert "You are playing as England." in prompt
        assert "England: 1 (A lon)" in prompt
        assert "Channel: Public Press (public)" in prompt
        assert "France: Hello England" in prompt

    def test_unknown_channel_raises(self):
        with pytest.raises(ContextError):
            reply_user_prompt(self._reply_context(), 99)
