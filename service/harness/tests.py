import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.migrations.loader import MigrationLoader
from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from inspect_ai import Task
from inspect_ai import eval as inspect_eval
from inspect_ai.dataset import MemoryDataset, Sample, json_dataset
from inspect_ai.log import EvalRevision
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Target
from inspect_ai.solver import generate

from common.constants import OrderType

from harness.adapter import data_to_fixture, fixture_to_context, fixture_to_data
from harness.constants import EvalRunKind
from harness.exceptions import ContextError, FixtureError, ParsingError, RecordingError
from harness.management.commands.sample_openings import ledger_for_nation
from harness.models import EvalRun, EvalScore
from harness.recorder import extract, write_migration
from harness.tasks.reply.parser import parse_completion as parse_reply
from harness.tasks.reply.user_prompt import user_prompt as reply_user_prompt
from harness.tasks.select_orders.evals import DATASET_PATH, fixture_to_sample, select_orders
from harness.tasks.select_orders.parser import parse_completion
from harness.tasks.select_orders.scorers import (
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


class TestDataToFixture:

    def _fixture(self, **overrides):
        fixture = {
            "id": "harvested_case",
            "variant": "classical",
            "nation": "Germany",
            "phase": {"season": "Fall", "year": 1903, "type": "Movement"},
            "units": [
                {"type": "Army", "nation": "Germany", "province": "mun"},
                {"type": "Army", "nation": "France", "province": "bur", "dislodged": True},
            ],
            "supply_centers": [
                {"nation": "Germany", "province": "mun"},
                {"nation": "Germany", "province": "kie"},
            ],
            "order_options": [
                {"source": "kie", "order_type": "Support", "target": "mun", "aux": "mun"},
                {"source": "mun", "order_type": "Hold", "target": "mun"},
                {"source": "mun", "order_type": "Move", "target": "ruh"},
            ],
        }
        fixture.update(overrides)
        return fixture

    def test_round_trips_through_data(self):
        fixture = self._fixture()
        data = fixture_to_data(fixture)
        assert data_to_fixture(data, fixture_id="harvested_case") == fixture

    def test_round_trips_with_max_orders(self):
        fixture = self._fixture(max_orders=1)
        data = fixture_to_data(fixture)
        assert data_to_fixture(data, fixture_id="harvested_case") == fixture

    def test_notes_are_attached_when_provided(self):
        fixture = self._fixture()
        data = fixture_to_data(fixture)
        result = data_to_fixture(data, fixture_id="harvested_case", notes="a note")
        assert result["notes"] == "a note"

    def test_missing_current_user_raises(self):
        fixture = self._fixture()
        data = fixture_to_data(fixture)
        for member in data["game"]["members"]:
            member["is_current_user"] = False
        with pytest.raises(FixtureError):
            data_to_fixture(data, fixture_id="harvested_case")


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


class TestOpeningLedger:

    def _hold_fixture(self):
        return {
            "id": "ledger",
            "variant": "classical",
            "nation": "England",
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": [{"type": "Army", "nation": "England", "province": "lon"}],
            "supply_centers": [{"nation": "England", "province": "lon"}],
            "order_options": [
                {"source": "lon", "order_type": "Hold", "target": "lon"},
                {"source": "lon", "order_type": "Move", "target": "wal"},
            ],
        }

    def _support_fixture(self):
        return {
            "id": "ledger_support",
            "variant": "classical",
            "nation": "Germany",
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": [
                {"type": "Army", "nation": "Germany", "province": "kie"},
                {"type": "Army", "nation": "Germany", "province": "mun"},
            ],
            "supply_centers": [{"nation": "Germany", "province": "kie"}],
            "order_options": [
                {"source": "kie", "order_type": "Support", "target": "mun", "aux": "mun"},
                {"source": "kie", "order_type": "Hold", "target": "kie"},
                {"source": "mun", "order_type": "Hold", "target": "mun"},
                {"source": "mun", "order_type": "Move", "target": "ruh"},
            ],
        }

    def test_tallies_joint_sets_and_flags_holds(self):
        context = fixture_to_context(self._hold_fixture())
        completions = [_completion([("lon", 0)]), _completion([("lon", 0)]), _completion([("lon", 1)])]
        ledger = ledger_for_nation(context, completions)

        assert ledger["samples"] == 3
        top = ledger["order_sets"][0]
        assert top["orders"] == ["A lon Hold"]
        assert top["count"] == 2
        assert top["share"] == 0.667
        assert top["flags"] == ["hold:lon"]
        assert ledger["order_sets"][1]["flags"] == []

    def test_flags_dangling_support_of_own_unit(self):
        context = fixture_to_context(self._support_fixture())
        ledger = ledger_for_nation(context, [_completion([("kie", 0), ("mun", 1)])])
        assert "dangling_support:mun" in ledger["order_sets"][0]["flags"]

    def test_flags_support_of_foreign_unit_separately(self):
        fixture = {
            "id": "ledger_foreign",
            "variant": "classical",
            "nation": "Austria",
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": [{"type": "Fleet", "nation": "Austria", "province": "tri"}],
            "supply_centers": [{"nation": "Austria", "province": "tri"}],
            "order_options": [
                {"source": "tri", "order_type": "Support", "target": "ven", "aux": "ven"},
                {"source": "tri", "order_type": "Hold", "target": "tri"},
            ],
        }
        context = fixture_to_context(fixture)
        flags = ledger_for_nation(context, [_completion([("tri", 0)])])["order_sets"][0]["flags"]
        assert "support_foreign:ven" in flags
        assert not any(flag.startswith("dangling_support:") for flag in flags)

    def test_counts_unparseable_completions(self):
        context = fixture_to_context(self._hold_fixture())
        ledger = ledger_for_nation(context, ["not json at all", _completion([("lon", 0)])])
        assert ledger["unparseable"] == 1
        assert ledger["samples"] == 2

    def test_flags_self_bounce(self):
        fixture = {
            "id": "ledger_bounce",
            "variant": "classical",
            "nation": "England",
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": [
                {"type": "Fleet", "nation": "England", "province": "edi"},
                {"type": "Fleet", "nation": "England", "province": "lon"},
            ],
            "supply_centers": [{"nation": "England", "province": "lon"}],
            "order_options": [
                {"source": "edi", "order_type": "Move", "target": "nth"},
                {"source": "edi", "order_type": "Hold", "target": "edi"},
                {"source": "lon", "order_type": "Move", "target": "nth"},
                {"source": "lon", "order_type": "Hold", "target": "lon"},
            ],
        }
        context = fixture_to_context(fixture)
        flags = ledger_for_nation(context, [_completion([("edi", 0), ("lon", 0)])])["order_sets"][0]["flags"]
        assert "self_bounce:nth" in flags

    def test_flags_no_orders(self):
        context = fixture_to_context(self._hold_fixture())
        ledger = ledger_for_nation(context, [_completion([])])
        assert ledger["order_sets"][0]["flags"] == ["no_orders"]

    def _uncontestable_fixture(self, with_enemy=False):
        units = [
            {"type": "Fleet", "nation": "England", "province": "lon"},
            {"type": "Fleet", "nation": "England", "province": "edi"},
        ]
        if with_enemy:
            units.append({"type": "Fleet", "nation": "Germany", "province": "hol"})
        return {
            "id": "ledger_uncontestable",
            "variant": "classical",
            "nation": "England",
            "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
            "units": units,
            "supply_centers": [{"nation": "England", "province": "lon"}],
            "order_options": [
                {"source": "lon", "order_type": "Move", "target": "nth"},
                {"source": "lon", "order_type": "Hold", "target": "lon"},
                {"source": "edi", "order_type": "Support", "target": "nth", "aux": "lon"},
                {"source": "edi", "order_type": "Hold", "target": "edi"},
            ],
        }

    def test_flags_uncontestable_support(self):
        context = fixture_to_context(self._uncontestable_fixture())
        flags = ledger_for_nation(context, [_completion([("lon", 0), ("edi", 0)])])["order_sets"][0]["flags"]
        assert "uncontestable_support:nth" in flags

    def test_contested_support_is_not_flagged_uncontestable(self):
        context = fixture_to_context(self._uncontestable_fixture(with_enemy=True))
        flags = ledger_for_nation(context, [_completion([("lon", 0), ("edi", 0)])])["order_sets"][0]["flags"]
        assert not any(flag.startswith("uncontestable_support") for flag in flags)


def _load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestEvalRunRecorder:

    def _log(self, tmp_path, fixtures, scorers, choices=(("lon", 0),)):
        dataset_path = tmp_path / "dataset.json"
        dataset_path.write_text(json.dumps(fixtures))
        model = get_model(
            "mockllm/model",
            custom_outputs=lambda *args, **kwargs: ModelOutput.from_content(
                "mockllm/model", _completion(list(choices))
            ),
        )
        task = Task(
            dataset=json_dataset(str(dataset_path), fixture_to_sample),
            solver=generate(),
            scorer=list(scorers),
        )
        log = inspect_eval(task, model=model, display="none", log_dir=str(tmp_path / "logs"))[0]
        log.eval.revision = EvalRevision(type="git", origin="origin", commit="abc1234", dirty=False)
        return log

    def _ranked_and_unranked(self, tmp_path):
        return self._log(
            tmp_path,
            [_quality_fixture("ranked"), _quality_fixture("unranked", ranked=False)],
            [legality(), quality_strong()],
        )

    def test_maps_the_log_onto_a_run_row(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        run = extract(log)["run"]
        assert run["kind"] == EvalRunKind.EVAL
        assert run["model"] == "mockllm/model"
        assert run["commit"] == "abc1234"
        assert run["epochs"] == 1
        assert run["eval_id"] == log.eval.eval_id
        assert run["ran_at"] == parse_datetime(log.eval.created)

    def test_records_the_given_model_over_the_log_model(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        assert extract(log, model="dumbbot")["run"]["model"] == "dumbbot"

    def test_digests_the_dataset_file(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        digest = hashlib.sha256((tmp_path / "dataset.json").read_bytes()).hexdigest()[:12]
        assert extract(log)["run"]["dataset"] == digest

    def test_digests_a_dataset_location_relative_to_the_task_file(self, tmp_path):
        model = get_model(
            "mockllm/model",
            custom_outputs=lambda *args, **kwargs: ModelOutput.from_content("mockllm/model", '{"choices": []}'),
        )
        log = inspect_eval(select_orders(), model=model, display="none", log_dir=str(tmp_path / "logs"))[0]
        log.eval.revision = EvalRevision(type="git", origin="origin", commit="abc1234", dirty=False)
        assert not Path(log.eval.dataset.location).is_absolute()

        digest = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()[:12]
        assert extract(log)["run"]["dataset"] == digest

    def test_refuses_a_log_without_results(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        log.results = None
        with pytest.raises(RecordingError):
            extract(log)

    def test_takes_sample_count_from_scored_samples(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        scores = {score["scorer"]: score for score in extract(log)["scores"]}
        assert scores["legality"]["sample_count"] == 2
        assert scores["quality_strong"]["sample_count"] == 1

    def test_carries_value_and_stderr_on_one_row_per_scorer(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        scores = extract(log)["scores"]
        assert [score["metric"] for score in scores] == ["accuracy", "accuracy"]
        assert all(score["value"] == 1.0 and score["stderr"] == 0.0 for score in scores)

    def test_drops_a_scorer_with_no_scored_samples(self, tmp_path):
        log = self._log(tmp_path, [_quality_fixture("unranked", ranked=False)], [legality(), quality_strong()])
        assert [score["scorer"] for score in extract(log)["scores"]] == ["legality"]

    def test_refuses_a_dirty_tree(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        log.eval.revision.dirty = True
        with pytest.raises(RecordingError):
            extract(log)

    def test_refuses_a_log_without_a_revision(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        log.eval.revision = None
        with pytest.raises(RecordingError):
            extract(log)

    def test_refuses_an_unsuccessful_log(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        log.status = "error"
        with pytest.raises(RecordingError):
            extract(log)

    def test_names_the_migration_after_the_model_and_commit(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        path = write_migration(extract(log, model="anthropic/claude-haiku-4-5"), directory=tmp_path)
        assert path.name == "0001_record_claude_haiku_4_5_abc1234.py"

    def test_numbers_the_migration_after_the_highest_existing_one(self, tmp_path):
        (tmp_path / "0007_something.py").write_text("")
        log = self._ranked_and_unranked(tmp_path)
        path = write_migration(extract(log, model="dumbbot"), directory=tmp_path)
        assert path.name == "0008_record_dumbbot_abc1234.py"

    def test_depends_on_the_current_harness_leaf(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        path = write_migration(extract(log), directory=tmp_path)
        leaf = MigrationLoader(None, ignore_no_migrations=True).graph.leaf_nodes("harness")[0][1]
        assert f'("harness", "{leaf}")' in path.read_text()

    @pytest.mark.django_db
    def test_generated_migration_records_the_run(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        module = _load_module(write_migration(extract(log, model="dumbbot"), directory=tmp_path))

        module.record(django_apps, None)

        run = EvalRun.objects.get()
        assert run.model == "dumbbot"
        assert run.commit == "abc1234"
        assert sorted(run.scores.values_list("scorer", "sample_count")) == [
            ("legality", 2),
            ("quality_strong", 1),
        ]

    @pytest.mark.django_db
    def test_generated_migration_unrecords_the_run(self, tmp_path):
        log = self._ranked_and_unranked(tmp_path)
        module = _load_module(write_migration(extract(log), directory=tmp_path))
        module.record(django_apps, None)

        module.unrecord(django_apps, None)

        assert not EvalRun.objects.exists()
        assert not EvalScore.objects.exists()


class TestRunEvalsCommand:

    def test_rejects_recording_a_limited_run(self):
        with pytest.raises(CommandError):
            call_command("run_evals", "--task", "dumbbot", "--record", "--limit", "1")

    def test_rejects_recording_a_zero_limited_run(self):
        with pytest.raises(CommandError):
            call_command("run_evals", "--task", "dumbbot", "--record", "--limit", "0")


class TestEvalScoreModel:

    @pytest.mark.django_db
    def test_rejects_a_duplicate_scorer_and_metric(self):
        run = EvalRun.objects.create(
            model="dumbbot", commit="abc1234", dataset="0123456789ab", epochs=1, ran_at=timezone.now()
        )
        EvalScore.objects.create(run=run, scorer="legality", metric="accuracy", value=1.0, sample_count=10)

        with pytest.raises(IntegrityError):
            EvalScore.objects.create(run=run, scorer="legality", metric="accuracy", value=0.5, sample_count=10)
