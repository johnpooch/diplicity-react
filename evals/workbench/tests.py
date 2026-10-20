import json
import shutil
from pathlib import Path

import pytest
from inspect_ai import Task
from inspect_ai import eval as inspect_eval
from inspect_ai.dataset import MemoryDataset
from inspect_ai.log import read_eval_log, write_eval_log
from inspect_ai.model import ModelOutput, ModelUsage, get_model
from inspect_ai.solver import solver

from games.evals import play_game
from games.reference import write_reference
from select_orders.evals import fixture_to_sample
from select_orders.fixtures import read_fixture, write_fixture

FIXTURE = {
    "schema_version": 2,
    "id": "paris_opening",
    "provenance": {"source": "handbuilt"},
    "variant": "classical",
    "nation": "France",
    "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
    "units": [
        {"type": "Army", "nation": "France", "province": "par"},
        {"type": "Fleet", "nation": "France", "province": "bre"},
    ],
    "supply_centers": [{"nation": "France", "province": "par"}],
    "order_options": [
        {"source": "bre", "order_type": "Hold"},
        {"source": "bre", "order_type": "Move", "target": "mid"},
        {"source": "par", "order_type": "Hold"},
        {"source": "par", "order_type": "Move", "target": "bur"},
    ],
    "eval_sets": ["opening"],
}

ATTACK = ["bre:Move:mid", "par:Move:bur"]
SIT = ["bre:Hold", "par:Hold"]
MIXED = ["bre:Hold", "par:Move:bur"]


@solver
def _scripted_solver(completions):
    async def solve(state, generate):
        state.output = ModelOutput.from_content(model="scripted", content=completions[state.epoch - 1])
        return state

    return solve


def _completion(option_ids, reasoning="because"):
    return json.dumps({"reasoning": reasoning, "choices": [{"option_id": chosen} for chosen in option_ids]})


@pytest.fixture
def fixtures_dir(tmp_path, settings):
    settings.EVALS_FIXTURES_DIR = tmp_path / "fixtures"
    settings.EVALS_FIXTURES_DIR.mkdir()
    settings.EVALS_LOGS_DIR = tmp_path / "logs"
    settings.EVALS_LOGS_DIR.mkdir()
    settings.EVALS_LABELLER = "tester"
    settings.EVALS_EVAL_SET = "opening"
    write_fixture(settings.EVALS_FIXTURES_DIR / "paris_opening.json", FIXTURE)
    return settings.EVALS_FIXTURES_DIR


@pytest.fixture
def run(fixtures_dir, settings):
    def _run(*completions, name="select_orders", fixtures=(FIXTURE,), prompt=None):
        task = Task(
            dataset=MemoryDataset([fixture_to_sample(fixture) for fixture in fixtures]),
            solver=_scripted_solver(completions),
            name=name,
        )
        log = inspect_eval(
            task,
            model="mockllm/model",
            epochs=len(completions),
            log_dir=str(settings.EVALS_LOGS_DIR),
            display="none",
            metadata={"prompt": {"name": prompt, "digest": "0" * 64}} if prompt else None,
        )[0]
        return log.location.rsplit("/", 1)[-1].removesuffix(".eval")

    return _run


def _label(client, orders, label, fixture="paris_opening", **extra):
    return client.post(
        f"/api/fixtures/{fixture}/order-set-labels/",
        data=json.dumps({"orders": orders, "label": label, **extra}),
        content_type="application/json",
    )


class TestFixtureList:

    def test_lists_fixtures_with_their_label_counts(self, client, fixtures_dir):
        _label(client, SIT, "unreasonable")
        assert client.get("/api/fixtures/").json() == {
            "fixtures": [
                {
                    "id": "paris_opening",
                    "nation": "France",
                    "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
                    "labels": {"unreasonable": 1},
                }
            ]
        }

    def test_leaves_out_fixtures_outside_the_eval_set(self, client, fixtures_dir):
        write_fixture(fixtures_dir / "other.json", {**FIXTURE, "id": "other", "eval_sets": ["elsewhere"]})
        assert [fixture["id"] for fixture in client.get("/api/fixtures/").json()["fixtures"]] == ["paris_opening"]


class TestFixtureDetail:

    def test_unknown_fixture_is_not_found(self, client, fixtures_dir):
        assert client.get("/api/fixtures/nowhere/").status_code == 404

    def test_returns_the_board_and_the_legal_options(self, client, fixtures_dir):
        detail = client.get("/api/fixtures/paris_opening/").json()
        assert detail["nation"] == "France"
        assert {unit["province"] for unit in detail["units"]} == {"par", "bre"}
        assert detail["options"] == ["bre:Hold", "bre:Move:mid", "par:Hold", "par:Move:bur"]
        assert detail["orders"]["par:Move:bur"]["source_name"] == "Paris"
        assert detail["orders"]["par:Move:bur"]["description"] == "Move -> Burgundy"

    def test_returns_only_labelled_order_sets_named_by_their_content(self, client, fixtures_dir):
        assert client.get("/api/fixtures/paris_opening/").json()["order_sets"] == []
        _label(client, ["par:Move:bur", "bre:Move:mid"], "reasonable", reason="the standard opening")
        assert client.get("/api/fixtures/paris_opening/").json()["order_sets"] == [
            {"orders": ATTACK, "name": "F Bre–MID · A Par–Bur", "label": "reasonable", "reason": "the standard opening"}
        ]

    def test_label_without_a_reason_has_an_empty_one(self, client, fixtures_dir):
        _label(client, SIT, "unreasonable")
        assert client.get("/api/fixtures/paris_opening/").json()["order_sets"][0]["reason"] == ""


class TestOrderSetLabels:

    def test_label_is_written_to_the_fixture_file(self, client, fixtures_dir):
        response = _label(client, ATTACK, "reasonable", reason=" the standard opening ")
        assert response.status_code == 200
        (entry,) = read_fixture(fixtures_dir / "paris_opening.json")["order_set_labels"]
        assert entry["orders"] == ATTACK
        assert entry["label"] == "reasonable"
        assert entry["labeller"] == "tester"
        assert entry["reason"] == "the standard opening"

    def test_reason_is_optional(self, client, fixtures_dir):
        _label(client, ATTACK, "reasonable")
        (entry,) = read_fixture(fixtures_dir / "paris_opening.json")["order_set_labels"]
        assert "reason" not in entry

    def test_relabelling_replaces_the_label_and_its_reason(self, client, fixtures_dir):
        _label(client, ATTACK, "reasonable", reason="first thought")
        _label(client, ATTACK, "unreasonable", reason="second thought")
        (entry,) = read_fixture(fixtures_dir / "paris_opening.json")["order_set_labels"]
        assert (entry["label"], entry["reason"]) == ("unreasonable", "second thought")

    def test_unknown_or_missing_label_is_rejected(self, client, fixtures_dir):
        assert _label(client, ATTACK, "fine").status_code == 400
        assert _label(client, ATTACK, None).status_code == 400

    def test_non_string_reason_is_rejected(self, client, fixtures_dir):
        assert _label(client, ATTACK, "reasonable", reason=3).status_code == 400

    def test_malformed_option_id_is_rejected_and_nothing_is_written(self, client, fixtures_dir):
        assert _label(client, ["par"], "reasonable").status_code == 400
        assert "order_set_labels" not in read_fixture(fixtures_dir / "paris_opening.json")

    def test_orders_must_be_a_list_of_ids(self, client, fixtures_dir):
        assert _label(client, "par:Move:bur", "reasonable").status_code == 400

    def test_unknown_fixture_is_not_found(self, client, fixtures_dir):
        assert _label(client, ATTACK, "reasonable", fixture="nowhere").status_code == 404

    def test_get_is_not_allowed(self, client, fixtures_dir):
        assert client.get("/api/fixtures/paris_opening/order-set-labels/").status_code == 405


class TestRunList:

    def test_lists_runs(self, client, run):
        name = run(_completion(ATTACK))
        (listed,) = client.get("/api/runs/").json()["runs"]
        assert listed["name"] == name
        assert listed["model"] == "mockllm/model"

    def test_run_carries_its_prompt_name(self, client, run):
        name = run(_completion(ATTACK), prompt="calm-lantern-oct-15")
        (listed,) = client.get("/api/runs/").json()["runs"]
        assert listed["prompt"] == "calm-lantern-oct-15"
        assert client.get(f"/api/runs/{name}/").json()["prompt"] == "calm-lantern-oct-15"

    def test_run_from_before_prompt_names_has_none(self, client, run):
        run(_completion(ATTACK))
        (listed,) = client.get("/api/runs/").json()["runs"]
        assert listed["prompt"] is None

    def test_lists_runs_with_their_score_and_fixtures(self, client, fixtures_dir, run):
        other = {**FIXTURE, "id": "second_opening"}
        write_fixture(fixtures_dir / "second_opening.json", other)
        run(_completion(ATTACK), _completion(SIT), "not json", fixtures=(FIXTURE, other))
        _label(client, ATTACK, "reasonable")
        (listed,) = client.get("/api/runs/").json()["runs"]
        assert listed["fixture_ids"] == ["paris_opening", "second_opening"]
        assert (listed["answers"], listed["failed"], listed["reasonable"], listed["unmarked"]) == (6, 2, 1, 3)
        assert listed["score"] == 0.25

    def test_listed_score_follows_a_relabel(self, client, run):
        run(_completion(ATTACK))
        assert client.get("/api/runs/").json()["runs"][0]["score"] == 0
        _label(client, ATTACK, "reasonable")
        assert client.get("/api/runs/").json()["runs"][0]["score"] == 1
        _label(client, ATTACK, "unreasonable")
        assert client.get("/api/runs/").json()["runs"][0]["score"] == 0

    def test_leaves_out_runs_of_other_tasks(self, client, run):
        name = run(_completion(ATTACK), name="dumbbot_select_orders")
        assert client.get("/api/runs/").json()["runs"] == []
        assert client.get(f"/api/runs/{name}/").status_code == 404

    def test_leaves_out_runs_that_did_not_succeed(self, client, run, settings):
        name = run(_completion(ATTACK))
        path = settings.EVALS_LOGS_DIR / f"{name}.eval"
        log = read_eval_log(str(path))
        log.status = "error"
        write_eval_log(log, str(path))
        assert client.get("/api/runs/").json()["runs"] == []


class TestRunScore:

    def _fixture_summary(self, client, name):
        (fixture,) = client.get(f"/api/runs/{name}/").json()["fixtures"]
        return fixture

    def test_unknown_run_is_not_found(self, client, fixtures_dir):
        assert client.get("/api/runs/nowhere/").status_code == 404

    def test_score_is_the_share_of_answers_whose_order_set_is_labelled_reasonable(self, client, run):
        name = run(_completion(ATTACK), _completion(ATTACK), _completion(ATTACK), _completion(SIT))
        _label(client, ATTACK, "reasonable")
        _label(client, SIT, "unreasonable")
        summary = self._fixture_summary(client, name)
        assert (summary["reasonable"], summary["unreasonable"], summary["score"]) == (3, 1, 0.75)
        assert summary["order_sets"] == 2

    def test_the_same_orders_in_another_sequence_are_one_order_set(self, client, run):
        name = run(_completion(ATTACK), _completion(list(reversed(ATTACK))))
        assert self._fixture_summary(client, name)["order_sets"] == 1

    def test_unmarked_answers_count_against_the_score(self, client, run):
        name = run(_completion(ATTACK), _completion(SIT), _completion(SIT))
        _label(client, ATTACK, "reasonable")
        summary = self._fixture_summary(client, name)
        assert (summary["score"], summary["unmarked"], summary["new"]) == (1 / 3, 2, 1)

    def test_labelling_after_the_run_changes_its_score(self, client, run):
        name = run(_completion(ATTACK))
        assert self._fixture_summary(client, name)["score"] == 0
        _label(client, ATTACK, "reasonable")
        assert self._fixture_summary(client, name)["score"] == 1

    def test_failed_answers_are_left_out_of_the_score(self, client, run):
        name = run(_completion(ATTACK), "not json")
        _label(client, ATTACK, "reasonable")
        summary = self._fixture_summary(client, name)
        assert (summary["answers"], summary["failed"], summary["score"]) == (2, 1, 1)

    def test_run_carries_its_id_and_epochs(self, client, run, settings):
        name = run(_completion(ATTACK), _completion(SIT))
        log = read_eval_log(str(settings.EVALS_LOGS_DIR / f"{name}.eval"), header_only=True)
        detail = client.get(f"/api/runs/{name}/").json()
        assert (detail["id"], detail["epochs"]) == (log.eval.eval_id, 2)

    def test_tokens_are_summed_over_answers(self, client, run, settings):
        name = run(_completion(ATTACK), _completion(SIT))
        path = settings.EVALS_LOGS_DIR / f"{name}.eval"
        log = read_eval_log(str(path))
        for sample in log.samples:
            sample.model_usage = {"m": ModelUsage(input_tokens=100, output_tokens=10, total_tokens=110)}
        write_eval_log(log, str(path))
        summary = self._fixture_summary(client, name)
        assert (summary["input_tokens"], summary["output_tokens"]) == (200, 20)

    def test_input_tokens_include_cached_prompt(self, client, run, settings):
        name = run(_completion(ATTACK), _completion(SIT))
        path = settings.EVALS_LOGS_DIR / f"{name}.eval"
        log = read_eval_log(str(path))
        log.samples[0].model_usage = {
            "m": ModelUsage(input_tokens=3, output_tokens=10, total_tokens=1013, input_tokens_cache_write=1000)
        }
        log.samples[1].model_usage = {
            "m": ModelUsage(input_tokens=3, output_tokens=10, total_tokens=1013, input_tokens_cache_read=1000)
        }
        write_eval_log(log, str(path))
        assert self._fixture_summary(client, name)["input_tokens"] == 2006

    def test_run_with_no_usable_answer_has_no_score(self, client, run):
        assert self._fixture_summary(client, run("not json"))["score"] is None

    def test_run_totals_add_up_its_fixtures(self, client, fixtures_dir, run):
        other = {**FIXTURE, "id": "second_opening"}
        write_fixture(fixtures_dir / "second_opening.json", other)
        name = run(_completion(ATTACK), _completion(SIT), fixtures=(FIXTURE, other))
        _label(client, ATTACK, "reasonable")
        detail = client.get(f"/api/runs/{name}/").json()
        assert [fixture["id"] for fixture in detail["fixtures"]] == ["paris_opening", "second_opening"]
        assert (detail["answers"], detail["reasonable"], detail["new"], detail["score"]) == (4, 1, 3, 0.25)


class TestRunQueue:

    def _queue(self, client, name):
        return client.get(f"/api/runs/{name}/queue/").json()

    def test_unknown_run_is_not_found(self, client, fixtures_dir):
        assert client.get("/api/runs/nowhere/queue/").status_code == 404

    def test_queue_holds_only_unlabelled_order_sets(self, client, run):
        name = run(_completion(ATTACK), _completion(SIT), _completion(MIXED))
        _label(client, ATTACK, "reasonable")
        _label(client, SIT, "unreasonable")
        queue = self._queue(client, name)
        assert [item["orders"] for item in queue["items"]] == [MIXED]
        assert queue["matched"] == 2

    def test_labelling_an_item_takes_it_out_of_the_queue(self, client, run):
        name = run(_completion(ATTACK))
        assert len(self._queue(client, name)["items"]) == 1
        _label(client, ATTACK, "unreasonable")
        assert self._queue(client, name) == {"matched": 1, "items": []}

    def test_item_carries_its_fixture_its_name_and_its_orders(self, client, run):
        (item,) = self._queue(client, run(_completion(ATTACK)))["items"]
        assert item["fixture"]["id"] == "paris_opening"
        assert {unit["province"] for unit in item["fixture"]["units"]} == {"par", "bre"}
        assert item["name"] == "F Bre–MID · A Par–Bur"
        assert item["details"]["par:Move:bur"]["description"] == "Move -> Burgundy"

    def test_item_carries_the_reasoning_of_every_epoch_that_produced_it(self, client, run):
        name = run(_completion(ATTACK, "attack"), _completion(SIT, "wait"), _completion(ATTACK, "attack again"))
        attack, sit = self._queue(client, name)["items"]
        assert attack["reasonings"] == [
            {"epoch": 1, "reasoning": "attack"},
            {"epoch": 3, "reasoning": "attack again"},
        ]
        assert sit["reasonings"] == [{"epoch": 2, "reasoning": "wait"}]

    def test_queue_runs_across_every_fixture_in_the_run(self, client, fixtures_dir, run):
        other = {**FIXTURE, "id": "second_opening"}
        write_fixture(fixtures_dir / "second_opening.json", other)
        name = run(_completion(ATTACK), fixtures=(FIXTURE, other))
        _label(client, ATTACK, "reasonable")
        assert [item["fixture"]["id"] for item in self._queue(client, name)["items"]] == ["second_opening"]


class TestRunFixture:

    def _detail(self, client, name, fixture="paris_opening"):
        return client.get(f"/api/runs/{name}/fixtures/{fixture}/")

    def test_unknown_run_or_fixture_is_not_found(self, client, run):
        name = run(_completion(ATTACK))
        assert self._detail(client, "nowhere").status_code == 404
        assert self._detail(client, name, "second_opening").status_code == 404

    def test_lists_every_order_set_the_run_produced_with_its_label(self, client, run):
        name = run(_completion(SIT, "wait"), _completion(ATTACK, "attack"), _completion(ATTACK, "again"))
        _label(client, ATTACK, "reasonable", reason="takes ground")
        attack, sit = self._detail(client, name).json()["order_sets"]
        assert (attack["orders"], attack["label"], attack["reason"], attack["epochs"]) == (
            ATTACK,
            "reasonable",
            "takes ground",
            [2, 3],
        )
        assert [entry["reasoning"] for entry in attack["reasonings"]] == ["attack", "again"]
        assert (sit["label"], sit["reason"], sit["epochs"]) == (None, "", [1])

    def test_order_set_carries_its_name_and_its_orders(self, client, run):
        (entry,) = self._detail(client, run(_completion(ATTACK))).json()["order_sets"]
        assert entry["name"] == "F Bre–MID · A Par–Bur"
        assert entry["details"]["par:Move:bur"]["description"] == "Move -> Burgundy"

    def test_carries_the_board_and_the_summary(self, client, run):
        detail = self._detail(client, run(_completion(ATTACK), "not json")).json()
        assert detail["fixture"]["id"] == "paris_opening"
        assert (detail["summary"]["answers"], detail["summary"]["failed"]) == (2, 1)

    def test_unusable_answers_carry_their_problem_and_completion(self, client, run):
        name = run(_completion(ATTACK), _completion(["par:Move:mar"]))
        (unusable,) = self._detail(client, name).json()["unusable"]
        assert unusable["epoch"] == 2
        assert unusable["problem"] == "unknown option id 'par:Move:mar'"
        assert "par:Move:mar" in unusable["completion"]


class TestRunPrompts:

    def test_unknown_run_is_not_found(self, client, fixtures_dir):
        assert client.get("/api/runs/nowhere/prompts/").status_code == 404

    def test_returns_the_prompts_as_sent_once_per_fixture(self, client, run):
        name = run(_completion(ATTACK), _completion(SIT))
        (prompts,) = client.get(f"/api/runs/{name}/prompts/").json()["prompts"]
        assert prompts["fixture"] == "paris_opening"
        assert prompts["system"].startswith("You are an expert Diplomacy player.")
        assert "You are playing as France." in prompts["user"]


OPENING_MOVE = "lon:Move:nth"


def _game_output(content):
    output = ModelOutput.from_content("mockllm/model", content)
    output.usage = ModelUsage(input_tokens=10, output_tokens=5, total_tokens=15)
    return output


def _game_answer(messages, *args):
    user = messages[-1].text
    if "Spring 1901, Movement" in user:
        return _game_output(_completion([OPENING_MOVE], "go north"))
    if "Fall 1901, Movement" in user:
        return _game_output("not json")
    return _game_output(_completion([]))


@pytest.fixture(scope="session")
def game_log(tmp_path_factory):
    (log,) = inspect_eval(
        play_game("England", 0, 2),
        model=get_model("mockllm/model", custom_outputs=_game_answer),
        display="none",
        log_dir=str(tmp_path_factory.mktemp("game_logs")),
        metadata={"prompt": {"name": "calm-lantern-oct-15", "digest": "0" * 64}},
    )
    return Path(log.location)


@pytest.fixture
def game_run(game_log, fixtures_dir, settings, tmp_path):
    settings.EVALS_FEEDBACK_DIR = tmp_path / "feedback"
    settings.EVALS_REFERENCE_DIR = tmp_path / "reference"
    shutil.copy(game_log, settings.EVALS_LOGS_DIR)
    return game_log.stem


def _note(client, run, seed, phase, note):
    return client.put(
        f"/api/games/{run}/{seed}/feedback/",
        data=json.dumps({"phase": phase, "note": note}),
        content_type="application/json",
    )


def _game(client, run, seed=0):
    return client.get(f"/api/games/{run}/{seed}/").json()


class TestGameRunList:

    def test_lists_game_runs_with_their_mean_result(self, client, game_run):
        (listed,) = client.get("/api/games/").json()["runs"]
        rows = client.get(f"/api/games/{game_run}/").json()["games"]
        assert (listed["name"], listed["nation"], listed["games"]) == (game_run, "England", 2)
        assert (listed["model"], listed["prompt"]) == ("mockllm/model", "calm-lantern-oct-15")
        assert listed["centres"] == pytest.approx(sum(row["centres"] for row in rows) / 2)
        assert listed["share"] == pytest.approx(sum(row["share"] for row in rows) / 2)

    def test_game_runs_and_order_runs_are_listed_apart(self, client, game_run, run):
        order_run = run(_completion(ATTACK))
        assert [listed["name"] for listed in client.get("/api/runs/").json()["runs"]] == [order_run]
        assert [listed["name"] for listed in client.get("/api/games/").json()["runs"]] == [game_run]

    def test_carries_the_dumbbot_reference_for_the_nation(self, client, game_run, settings):
        assert client.get("/api/games/").json()["references"] == {"England": None}
        games = [{"seed": 0, "centres": 5, "share": 12.5}, {"seed": 1, "centres": 6, "share": 16.0}]
        write_reference(settings.EVALS_REFERENCE_DIR, "England", games)
        assert client.get("/api/games/").json()["references"] == {"England": {"games": games}}

    def test_counts_the_games_with_feedback(self, client, game_run):
        assert client.get("/api/games/").json()["runs"][0]["with_feedback"] == 0
        _note(client, game_run, 1, None, "Too passive.")
        assert client.get("/api/games/").json()["runs"][0]["with_feedback"] == 1

    def test_feedback_without_its_game_is_reported(self, client, game_run, settings):
        for path in ("gone/0.json", f"{game_run}/9.json"):
            (settings.EVALS_FEEDBACK_DIR / path).parent.mkdir(parents=True, exist_ok=True)
            (settings.EVALS_FEEDBACK_DIR / path).write_text(json.dumps({"nation": "England", "overall": "note"}))
        assert client.get("/api/games/").json()["orphans"] == [
            {"path": f"feedback/{game_run}/9.json", "problem": f"game run '{game_run}' has no game with seed 9"},
            {"path": "feedback/gone/0.json", "problem": "no game run 'gone' in the logs"},
        ]

    def test_invalid_feedback_file_is_reported(self, client, game_run, settings):
        path = settings.EVALS_FEEDBACK_DIR / game_run / "0.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"nation": "England", "score": 3}))
        (orphan,) = client.get("/api/games/").json()["orphans"]
        assert "violates schema" in orphan["problem"]


class TestGameRunDetail:

    def test_unknown_run_is_not_found(self, client, game_run, run):
        assert client.get("/api/games/nowhere/").status_code == 404
        assert client.get(f"/api/games/{run(_completion(ATTACK))}/").status_code == 404

    def test_lists_each_game_with_its_result_and_the_paired_game(self, client, game_run):
        detail = client.get(f"/api/games/{game_run}/").json()
        assert detail["nation"] == "England"
        assert [row["seed"] for row in detail["games"]] == [0, 1]
        row = detail["games"][0]
        assert row["end"] == "horizon"
        assert row["failed"] == 1
        assert 0 <= row["share"] <= 100 and 0 <= row["paired_share"] <= 100
        assert isinstance(row["centres"], int) and isinstance(row["paired_centres"], int)

    def test_marks_the_games_with_feedback(self, client, game_run):
        _note(client, game_run, 1, None, "Too passive.")
        assert [row["feedback"] for row in client.get(f"/api/games/{game_run}/").json()["games"]] == [False, True]

    def test_carries_the_opening_prompt(self, client, game_run):
        opening = client.get(f"/api/games/{game_run}/").json()["opening"]
        assert opening["system"].startswith("You are an expert Diplomacy player.")
        assert "You are playing as England." in opening["user"]

    def test_carries_the_reference_for_its_nation(self, client, game_run, settings):
        assert client.get(f"/api/games/{game_run}/").json()["reference"] is None
        write_reference(settings.EVALS_REFERENCE_DIR, "England", [{"seed": 0, "centres": 5, "share": 12.5}])
        assert client.get(f"/api/games/{game_run}/").json()["reference"]["games"][0]["share"] == 12.5


class TestGameDetail:

    def test_unknown_game_is_not_found(self, client, game_run):
        assert client.get(f"/api/games/{game_run}/9/").status_code == 404
        assert client.get("/api/games/nowhere/0/").status_code == 404

    def test_lists_every_phase_from_the_opening_to_the_last_played(self, client, game_run):
        phases = _game(client, game_run)["phases"]
        assert (phases[0]["key"], phases[-1]["key"]) == ("1901-Spring-Movement", "1905-Fall-Retreat")
        assert len(phases) == 24

    def test_phase_carries_every_nation_orders_with_their_results(self, client, game_run):
        opening = _game(client, game_run)["phases"][0]
        assert {order["nation"] for order in opening["orders"]} == {
            "Austria",
            "England",
            "France",
            "Germany",
            "Italy",
            "Russia",
            "Turkey",
        }
        (london,) = [order for order in opening["orders"] if order["source"] == "lon"]
        assert (london["id"], london["description"], london["result"]) == (OPENING_MOVE, "Move -> North Sea", "OK")

    def test_phase_carries_the_model_answer_with_its_orders_named(self, client, game_run):
        answer = _game(client, game_run)["phases"][0]["answer"]
        assert (answer["reasoning"], answer["problem"]) == ("go north", None)
        assert [order["name"] for order in answer["orders"]] == ["F Lon–NTH"]
        assert answer["orders"][0]["result"] == "OK"
        assert "You are playing as England." in answer["user"]

    def test_failed_phase_carries_its_problem_and_raw_completion(self, client, game_run):
        fall = next(phase for phase in _game(client, game_run)["phases"] if phase["key"] == "1901-Fall-Movement")
        assert fall["answer"]["problem"].startswith("could not parse JSON")
        assert fall["answer"]["completion"] == "not json"
        assert fall["answer"]["orders"] == []
        assert not [order for order in fall["orders"] if order["nation"] == "England"]

    def test_phase_the_model_was_not_asked_has_no_answer(self, client, game_run):
        assert _game(client, game_run)["phases"][1]["answer"] is None

    def test_phase_names_the_units_its_resolution_dislodged(self, client, game_run):
        phases = _game(client, game_run)["phases"]
        for phase, following in zip(phases, phases[1:]):
            assert phase["dislodged"] == [unit["province"] for unit in following["units"] if unit["dislodged"]]

    def test_carries_the_final_centres_and_the_score(self, client, game_run):
        game = _game(client, game_run)
        assert set(game["final_centres"]) == {"Austria", "England", "France", "Germany", "Italy", "Russia", "Turkey"}
        assert game["centres"] == game["final_centres"]["England"]
        assert game["end"] == "horizon"

    def test_carries_its_feedback(self, client, game_run):
        assert _game(client, game_run)["feedback"] == {"overall": "", "phases": {}}
        _note(client, game_run, 0, "1902-Fall-Movement", "Left Norway open.")
        assert _game(client, game_run)["feedback"] == {
            "overall": "",
            "phases": {"1902-Fall-Movement": "Left Norway open."},
        }


class TestGameFeedback:

    def _file(self, settings, run, seed=0):
        return settings.EVALS_FEEDBACK_DIR / run / f"{seed}.json"

    def test_notes_are_written_to_the_game_feedback_file(self, client, game_run, settings):
        _note(client, game_run, 0, "1902-Fall-Movement", "Left Norway open.")
        response = _note(client, game_run, 0, None, "Too passive.")
        assert response.status_code == 200
        assert response.json() == {"overall": "Too passive.", "phases": {"1902-Fall-Movement": "Left Norway open."}}
        assert json.loads(self._file(settings, game_run).read_text()) == {
            "nation": "England",
            "overall": "Too passive.",
            "phases": {"1902-Fall-Movement": "Left Norway open."},
        }

    def test_phase_the_game_does_not_contain_is_rejected(self, client, game_run, settings):
        assert _note(client, game_run, 0, "1905-Fall-Adjustment", "note").status_code == 400
        assert not self._file(settings, game_run).exists()

    def test_emptied_note_is_removed_and_an_empty_file_deleted(self, client, game_run, settings):
        _note(client, game_run, 0, None, "Too passive.")
        _note(client, game_run, 0, "1902-Fall-Movement", "Left Norway open.")
        _note(client, game_run, 0, None, "")
        assert json.loads(self._file(settings, game_run).read_text()) == {
            "nation": "England",
            "phases": {"1902-Fall-Movement": "Left Norway open."},
        }
        _note(client, game_run, 0, "1902-Fall-Movement", "   ")
        assert not self._file(settings, game_run).exists()

    def test_malformed_body_is_rejected(self, client, game_run):
        url = f"/api/games/{game_run}/0/feedback/"
        assert client.put(url, data="nope", content_type="application/json").status_code == 400
        assert _note(client, game_run, 0, None, 3).status_code == 400
        assert _note(client, game_run, 0, 1902, "note").status_code == 400

    def test_unknown_game_is_not_found(self, client, game_run):
        assert _note(client, game_run, 9, None, "note").status_code == 404

    def test_only_put_is_allowed(self, client, game_run):
        assert client.get(f"/api/games/{game_run}/0/feedback/").status_code == 405
