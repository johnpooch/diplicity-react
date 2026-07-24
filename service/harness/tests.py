import json

import pytest

from common.constants import OrderType
from inspect_ai.scorer import CORRECT, INCORRECT, Target

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
from harness.evals.select_orders.select_orders_structure import (
    coverage,
    deduplication,
    legality,
    support_coherence,
    convoy_coherence,
)



# --- builders -------------------------------------------------------------
# Mirror the option shape produced by ContextBuilder.add_option. Only the
# fields the scorers read (source.id) need to be faithful; the rest are
# included so the fixtures look like real contexts.


def _option(source_id, order_type, target=None, aux=None, unit_type=None):
    def field(value):
        return {"id": value, "label": value} if value is not None else None

    return {
        "source": {"id": source_id, "label": source_id},
        "order_type": field(order_type),
        "target": field(target),
        "aux": field(aux),
        "unit_type": field(unit_type),
    }


def _context(options):
    # NOTE: confirm this key matches your ContextData ("order_options" here).
    return {"order_options": options}


class _FakeOutput:
    def __init__(self, completion):
        self.completion = completion


class _FakeState:
    """Minimal stand-in for TaskState.

    The scorers only ever read state.output.completion and
    state.metadata["context"], so we expose exactly those. This keeps the
    tests fast and free of TaskState's construction requirements while
    staying faithful to what the scorers actually touch.
    """

    def __init__(self, completion, context):
        self.output = _FakeOutput(completion)
        self.metadata = {"context": context}


def _state(selected_json, options):
    """Build a fake state from a raw completion string and an option list."""
    return _FakeState(selected_json, _context(options))


def _run(scorer_factory, state):
    """Invoke a scorer's async score() closure synchronously for testing.

    Scorers are async so they can participate in Inspect's scheduling, but
    ours never await anything, so we can drive the coroutine to completion
    with a single send() rather than pulling in an event loop.
    """
    score_fn = scorer_factory()
    coro = score_fn(state, Target(""))
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    raise AssertionError("scorer awaited something; expected it to be synchronous")


# --- shared fixtures ------------------------------------------------------
# The "structure" fixture: three provinces, two options each, in reading
# order. This is the happy-path fixture the eval already runs.

STRUCTURE_OPTIONS = [
    _option("lon", "Hold"),
    _option("lon", "Move", target="eng"),
    _option("par", "Hold"),
    _option("par", "Move", target="bur"),
    _option("ber", "Hold"),
    _option("ber", "Move", target="kie"),
]


# The adversarial fixture: one province (lon) has many attractive-looking
# options, another (par) has only a single dull Hold. This tempts a model to
# over-invest in lon and forget par -- the exact "two orders for London, none
# for Paris" failure that motivated separating dedup from coverage. Used here
# to prove the scorers go RED when they should, not to test the model.

LOPSIDED_OPTIONS = [
    _option("lon", "Hold"),
    _option("lon", "Move", target="eng"),
    _option("lon", "Move", target="wal"),
    _option("lon", "Support", aux="wal", target="lvp"),
    _option("par", "Hold"),
]


# --- legality -------------------------------------------------------------


class TestLegality:

    def test_in_range_selection_is_correct(self):
        state = _state(json.dumps({"selected": [0, 2, 4]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == CORRECT

    def test_out_of_range_index_is_incorrect(self):
        state = _state(json.dumps({"selected": [0, 2, 99]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT

    def test_negative_index_is_incorrect(self):
        state = _state(json.dumps({"selected": [-1]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT

    def test_non_integer_index_is_incorrect(self):
        state = _state(json.dumps({"selected": ["0"]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT

    def test_invalid_json_is_incorrect(self):
        state = _state("not json at all", STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT

    def test_missing_selected_key_is_incorrect(self):
        state = _state(json.dumps({"choices": [0]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT

    def test_non_list_selected_is_incorrect(self):
        state = _state(json.dumps({"selected": 0}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == INCORRECT


# --- deduplication --------------------------------------------------------


class TestDeduplication:

    def test_distinct_provinces_are_correct(self):
        state = _state(json.dumps({"selected": [0, 2, 4]}), STRUCTURE_OPTIONS)
        assert _run(deduplication, state).value == CORRECT

    def test_two_orders_for_same_province_is_incorrect(self):
        # indices 0 and 1 are both London
        state = _state(json.dumps({"selected": [0, 1, 2]}), STRUCTURE_OPTIONS)
        assert _run(deduplication, state).value == INCORRECT

    def test_out_of_range_index_is_ignored_by_dedup(self):
        # 99 is out of range (legality's problem); the in-range picks 0,2 are
        # distinct provinces, so dedup should still pass.
        state = _state(json.dumps({"selected": [0, 2, 99]}), STRUCTURE_OPTIONS)
        assert _run(deduplication, state).value == CORRECT

    def test_lopsided_over_selection_fails_dedup(self):
        # Two London picks (0,1) from the adversarial fixture.
        state = _state(json.dumps({"selected": [0, 1]}), LOPSIDED_OPTIONS)
        assert _run(deduplication, state).value == INCORRECT


# --- coverage -------------------------------------------------------------


class TestCoverage:

    def test_all_provinces_covered_is_correct(self):
        state = _state(json.dumps({"selected": [0, 2, 4]}), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == CORRECT

    def test_missing_province_is_incorrect(self):
        # covers lon and par, omits ber
        state = _state(json.dumps({"selected": [0, 2]}), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == INCORRECT

    def test_duplicate_that_drops_a_province_is_incorrect(self):
        # [0,1,2] is two Londons and one Paris -> Berlin uncovered
        state = _state(json.dumps({"selected": [0, 1, 2]}), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == INCORRECT

    def test_out_of_range_pick_does_not_count_as_coverage(self):
        # 99 covers nothing, so ber remains missing
        state = _state(json.dumps({"selected": [0, 2, 99]}), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == INCORRECT

    def test_lopsided_over_selection_fails_coverage(self):
        # Both picks are London; par is never covered.
        state = _state(json.dumps({"selected": [0, 1]}), LOPSIDED_OPTIONS)
        assert _run(coverage, state).value == INCORRECT


# --- the key cross-scorer case -------------------------------------------
# This is the response the happy-path fixture can never elicit but which the
# scorers must handle correctly: right count, all in range, but wrong shape.
# [0,1,2] on the structure fixture is legal, but is a dedup failure AND a
# coverage failure. Proving all three verdicts on one input is what tells us
# the three metrics are genuinely independent rather than measuring the same
# "did the obvious thing" event.


class TestRightCountWrongShape:

    def test_legality_passes(self):
        state = _state(json.dumps({"selected": [0, 1, 2]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == CORRECT

    def test_deduplication_fails(self):
        state = _state(json.dumps({"selected": [0, 1, 2]}), STRUCTURE_OPTIONS)
        assert _run(deduplication, state).value == INCORRECT

    def test_coverage_fails(self):
        state = _state(json.dumps({"selected": [0, 1, 2]}), STRUCTURE_OPTIONS)
        assert _run(coverage, state).value == INCORRECT

    
class TestMixed:

    def test_redundant_third_pick_fails_dedup_only(self):
        # [0,1,4] on the lopsided fixture: two Londons AND Paris.
        # This is the baseline rung-4 signature: coverage stays GREEN
        # (both provinces covered) while dedup goes RED.
        state = _state(json.dumps({"selected": [0, 1, 4]}), LOPSIDED_OPTIONS)
        assert _run(deduplication, state).value == INCORRECT
        assert _run(coverage, state).value == CORRECT


class TestFencedJson:
    def test_fenced_completion_parses(self):
        # model wrapped valid JSON in a markdown fence despite "no fences".
        # This is a harness concern (parser tolerance), not model judgment.
        state = _state('```json\n{"selected":[0,2,4]}\n```', STRUCTURE_OPTIONS)
        assert _run(legality, state).value == CORRECT

    def test_bare_json_still_parses(self):
        # regression guard: the fence-stripping must not break unfenced input.
        state = _state(json.dumps({"selected": [0, 2, 4]}), STRUCTURE_OPTIONS)
        assert _run(legality, state).value == CORRECT


# --- the support-coherence fixture ---------------------------------------
#   idx 0  London Move -> Liverpool     (the supported MOVE)
#   idx 1  London Hold                  (London stays put)
#   idx 2  Wales  Support London -> Lvp  (support-MOVE: coherent iff London moves to Lvp)
#   idx 3  Wales  Support London -> Lon  (support-HOLD: coherent iff London does NOT move)
#   idx 4  Wales  Hold                   (Wales opts out of supporting)

SUPPORT_OPTIONS = [
    _option("lon", "Move", target="lvp"),               # 0
    _option("lon", "Hold"),                              # 1
    _option("wal", "Support", aux="lon", target="lvp"),  # 2  support-move
    _option("wal", "Support", aux="lon", target="lon"),  # 3  support-hold
    _option("wal", "Hold"),                              # 4
]


class TestSupportMove:

    def test_supported_move_present_is_coherent(self):
        # [0,2]: London moves to Liverpool, Wales supports that move.
        state = _state(json.dumps({"selected": [0, 2]}), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == CORRECT

    def test_supported_move_absent_dangles(self):
        # [1,2]: Wales supports London->Lvp, but London HOLDS. Dangling move.
        state = _state(json.dumps({"selected": [1, 2]}), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == INCORRECT


class TestSupportHold:

    def test_supported_hold_present_is_coherent(self):
        # [1,3]: Wales support-holds London, London holds. Coherent.
        state = _state(json.dumps({"selected": [1, 3]}), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == CORRECT

    def test_supported_unit_moves_away_dangles_hold(self):
        # [0,3]: Wales support-holds London, but London MOVES to Lvp. The
        # support-hold dangles -- the unit left the province it was held in.
        # The case a naive "is the aux mentioned?" scorer gets wrong.
        state = _state(json.dumps({"selected": [0, 3]}), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == INCORRECT


class TestSupportAuxAbsent:

    def test_support_hold_with_aux_unselected_dangles(self):
        # [3]: Wales support-holds London, but London has no selected order.
        # Nothing keeps London in place, so the support dangles. RED here;
        # coverage separately reports London uncovered.
        state = _state(json.dumps({"selected": [3]}), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == INCORRECT


class TestNoSupportSelected:

    def test_no_support_selected_is_coherent(self):
        # [1,4]: no Support order selected, nothing to dangle. The scorer
        # answers ONE question and stays silent (GREEN) when it doesn't arise
        # -- same discipline as legality/dedup/coverage.
        state = _state(json.dumps({"selected": [1, 4]}), SUPPORT_OPTIONS)
        assert _run(support_coherence, state).value == CORRECT


# --- the convoy-coherence fixture ----------------------------------------
#   idx 0  Eng Convoy London -> Brest   (fleet convoys the army)
#   idx 1  Eng Hold
#   idx 2  London Move -> Brest          (the convoyed move)
#   idx 3  London Hold                   (army stays -> convoy dangles)

CONVOY_OPTIONS = [
    _option("eng", "Convoy", aux="lon", target="bre"),  # 0
    _option("eng", "Hold"),                              # 1
    _option("lon", "Move", target="bre"),               # 2
    _option("lon", "Hold"),                              # 3
]


class TestConvoyCoherence:

    def test_convoyed_move_present_is_coherent(self):
        # [0,2]: Eng convoys London->Brest, London moves to Brest. Coherent.
        state = _state(json.dumps({"selected": [0, 2]}), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == CORRECT

    def test_convoyed_army_holds_dangles(self):
        # [0,3]: Eng convoys London->Brest, but London HOLDS. Dangling convoy.
        state = _state(json.dumps({"selected": [0, 3]}), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == INCORRECT

    def test_convoyed_army_absent_dangles(self):
        # [0]: Eng convoys London, but London has no selected order at all.
        state = _state(json.dumps({"selected": [0]}), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == INCORRECT

    def test_no_convoy_selected_is_coherent(self):
        # [1,2]: no Convoy order selected, nothing to dangle. Silent green.
        state = _state(json.dumps({"selected": [1, 2]}), CONVOY_OPTIONS)
        assert _run(convoy_coherence, state).value == CORRECT