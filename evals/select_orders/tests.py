import json
import math

import pytest
from inspect_ai import Task
from inspect_ai import eval as inspect_eval
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Target
from inspect_ai.solver import generate

from select_orders.context import fixture_to_context
from select_orders.evals import dumbbot_select_orders, load_fixtures
from select_orders.exceptions import FixtureError, ParsingError
from select_orders.parser import parse_completion
from select_orders.scorers import (
    convoy_coherence,
    coverage,
    deduplication,
    legality,
    quality_avoidance,
    quality_strong,
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
    _option("lon", "Hold"),
    _option("lon", "Move", target="eng"),
    _option("par", "Hold"),
    _option("par", "Move", target="bur"),
    _option("ber", "Hold"),
    _option("ber", "Move", target="kie"),
]


class TestParseCompletion:

    def test_valid_choices_return_selected_options(self):
        completion = _completion([("lon", 0), ("par", 1), ("ber", 0)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [
            _option("lon", "Hold"),
            _option("par", "Move", target="bur"),
            _option("ber", "Hold"),
        ]

    def test_fenced_completion_parses(self):
        completion = f"```json\n{_completion([('lon', 0)])}\n```"
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("lon", "Hold")]

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
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("par", "Hold")]

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
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("lon", "Hold")]

    def test_last_choice_per_source_wins(self):
        completion = _completion([("lon", 0), ("lon", 1)])
        assert parse_completion(completion, _context(STRUCTURE_OPTIONS)) == [_option("lon", "Move", target="eng")]


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
    _option("lon", "Move", target="lvp"),
    _option("lon", "Hold"),
    _option("wal", "Support", aux="lon", target="lvp"),
    _option("wal", "Support", aux="lon", target="lon"),
    _option("wal", "Hold"),
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
    _option("eng", "Convoy", aux="lon", target="bre"),
    _option("eng", "Hold"),
    _option("lon", "Move", target="bre"),
    _option("lon", "Hold"),
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


def _quality_fixture(fixture_id="quality", ranked=True):
    fixture = {
        "id": fixture_id,
        "variant": "classical",
        "nation": "England",
        "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
        "units": [{"type": "Army", "nation": "England", "province": "lon"}],
        "supply_centers": [{"nation": "England", "province": "lon"}],
        "order_options": [
            {"source": "lon", "order_type": "Hold", "target": "lon"},
            {"source": "lon", "order_type": "Move", "target": "eng"},
        ],
    }
    if ranked:
        fixture["ranked_options"] = {
            "good": [{"source": "lon", "order_type": "Hold", "target": "lon"}],
            "neutral": [],
            "bad": [{"source": "lon", "order_type": "Move", "target": "eng"}],
        }
    return fixture


class TestQualityScorers:

    def _state(self, fixture, choices):
        state = _FakeState(_completion(choices), fixture_to_context(fixture))
        state.metadata["ranked_options"] = fixture.get("ranked_options")
        return state

    def test_selecting_good_order_is_strong_correct(self):
        assert _run(quality_strong, self._state(_quality_fixture(), [("lon", 0)])).value == CORRECT

    def test_missing_good_order_is_strong_incorrect(self):
        assert _run(quality_strong, self._state(_quality_fixture(), [("lon", 1)])).value == INCORRECT

    def test_selecting_bad_order_is_avoidance_incorrect(self):
        assert _run(quality_avoidance, self._state(_quality_fixture(), [("lon", 1)])).value == INCORRECT

    def test_avoiding_bad_order_is_avoidance_correct(self):
        assert _run(quality_avoidance, self._state(_quality_fixture(), [("lon", 0)])).value == CORRECT

    def test_fixture_without_ranked_options_is_unscored(self):
        state = self._state(_quality_fixture(ranked=False), [("lon", 0)])
        for scorer_factory in (quality_strong, quality_avoidance):
            value = _run(scorer_factory, state).value
            assert isinstance(value, float) and math.isnan(value)


class TestQualityMetricAggregation:

    def _sample(self, fixture):
        return Sample(
            id=fixture["id"],
            input="ignored",
            metadata={"context": fixture_to_context(fixture), "ranked_options": fixture.get("ranked_options")},
        )

    def test_accuracy_covers_ranked_samples_and_skips_the_rest(self, tmp_path):
        good_pick = _completion([("lon", 0)])
        model = get_model(
            "mockllm/model",
            custom_outputs=lambda *args, **kwargs: ModelOutput.from_content("mockllm/model", good_pick),
        )
        dataset = MemoryDataset(
            [
                self._sample(_quality_fixture("ranked", ranked=True)),
                self._sample(_quality_fixture("unranked", ranked=False)),
            ]
        )
        task = Task(dataset=dataset, solver=generate(), scorer=[quality_strong(), quality_avoidance()])
        log = inspect_eval(task, model=model, display="none", log_dir=str(tmp_path))[0]

        metrics = {score.name: score.metrics["accuracy"].value for score in log.results.scores}
        assert metrics["quality_strong"] == 1.0
        assert metrics["quality_avoidance"] == 1.0


class TestFixtureToContext:

    def test_eval_nation_is_the_current_member_and_listed_first(self):
        context = fixture_to_context(_quality_fixture())
        assert context["members"][0] == {"name": "England", "nation": "England", "is_current_user": True}

    def test_every_supply_centre_is_listed_with_its_owner_or_none(self):
        centers = {
            center["province"]: center["nation"] for center in fixture_to_context(_quality_fixture())["supply_centers"]
        }
        assert len(centers) == 34
        assert centers["lon"] == "England"
        assert centers["par"] is None

    def test_unknown_province_raises(self):
        fixture = _quality_fixture()
        fixture["order_options"].append({"source": "atlantis", "order_type": "Hold"})
        with pytest.raises(FixtureError):
            fixture_to_context(fixture)

    def test_unknown_variant_raises(self):
        with pytest.raises(FixtureError):
            fixture_to_context({**_quality_fixture(), "variant": "nonexistent"})


class TestFixtures:

    def test_every_fixture_builds_a_context(self):
        fixtures = load_fixtures()
        assert fixtures
        for fixture in fixtures:
            assert fixture_to_context(fixture)["order_options"]

    def test_every_fixture_declares_its_provenance(self):
        assert {fixture["provenance"]["source"] for fixture in load_fixtures()} == {"handbuilt"}


class TestDumbbotSelectOrders:

    def test_dumbbot_passes_every_structural_scorer(self, tmp_path):
        log = inspect_eval(dumbbot_select_orders(), model="mockllm/model", display="none", log_dir=str(tmp_path))[0]
        metrics = {score.name: score.metrics["accuracy"].value for score in log.results.scores}
        for name in ("legality", "deduplication", "coverage", "support_coherence", "convoy_coherence"):
            assert metrics[name] == 1.0
