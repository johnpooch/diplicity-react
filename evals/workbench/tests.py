import json

import pytest
from inspect_ai import Task
from inspect_ai import eval as inspect_eval
from inspect_ai.dataset import MemoryDataset
from inspect_ai.log import read_eval_log, write_eval_log
from inspect_ai.model import ModelOutput
from inspect_ai.solver import solver

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
    def _run(*completions, name="select_orders", fixtures=(FIXTURE,)):
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

    def test_score_is_the_share_of_distinct_order_sets_labelled_reasonable(self, client, run):
        name = run(_completion(ATTACK), _completion(ATTACK), _completion(ATTACK), _completion(SIT))
        _label(client, ATTACK, "reasonable")
        _label(client, SIT, "unreasonable")
        summary = self._fixture_summary(client, name)
        assert (summary["order_sets"], summary["reasonable"], summary["score"]) == (2, 1, 0.5)

    def test_the_same_orders_in_another_sequence_are_one_order_set(self, client, run):
        name = run(_completion(ATTACK), _completion(list(reversed(ATTACK))))
        assert self._fixture_summary(client, name)["order_sets"] == 1

    def test_unlabelled_order_sets_count_against_the_score_as_new(self, client, run):
        name = run(_completion(ATTACK), _completion(SIT))
        _label(client, ATTACK, "reasonable")
        summary = self._fixture_summary(client, name)
        assert (summary["score"], summary["new"], summary["matched"]) == (0.5, 1, 1)

    def test_labelling_after_the_run_changes_its_score(self, client, run):
        name = run(_completion(ATTACK))
        assert self._fixture_summary(client, name)["score"] == 0
        _label(client, ATTACK, "reasonable")
        assert self._fixture_summary(client, name)["score"] == 1

    def test_unusable_answers_are_counted_apart_from_order_sets(self, client, run):
        name = run(_completion(ATTACK), "not json")
        summary = self._fixture_summary(client, name)
        assert (summary["answers"], summary["order_sets"], summary["unanswered"]) == (2, 1, 1)

    def test_order_sets_split_into_reasonable_unreasonable_and_new(self, client, run):
        name = run(_completion(ATTACK), _completion(SIT), _completion(MIXED))
        _label(client, ATTACK, "reasonable")
        _label(client, SIT, "unreasonable")
        summary = self._fixture_summary(client, name)
        assert (summary["reasonable"], summary["unreasonable"], summary["new"]) == (1, 1, 1)

    def test_run_carries_its_id(self, client, run, settings):
        name = run(_completion(ATTACK))
        log = read_eval_log(str(settings.EVALS_LOGS_DIR / f"{name}.eval"), header_only=True)
        assert client.get(f"/api/runs/{name}/").json()["id"] == log.eval.eval_id

    def test_run_with_no_usable_answer_has_no_score(self, client, run):
        assert self._fixture_summary(client, run("not json"))["score"] is None

    def test_run_totals_add_up_its_fixtures(self, client, fixtures_dir, run):
        other = {**FIXTURE, "id": "second_opening"}
        write_fixture(fixtures_dir / "second_opening.json", other)
        name = run(_completion(ATTACK), _completion(SIT), fixtures=(FIXTURE, other))
        _label(client, ATTACK, "reasonable")
        detail = client.get(f"/api/runs/{name}/").json()
        assert [fixture["id"] for fixture in detail["fixtures"]] == ["paris_opening", "second_opening"]
        assert (detail["order_sets"], detail["reasonable"], detail["new"], detail["score"]) == (4, 1, 3, 0.25)


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
        assert (detail["summary"]["answers"], detail["summary"]["order_sets"], detail["summary"]["unanswered"]) == (
            2,
            1,
            1,
        )

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
