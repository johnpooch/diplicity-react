import asyncio
import json
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from inspect_ai import eval as inspect_eval
from inspect_ai.log import read_eval_log
from inspect_ai.model import ModelOutput, ModelUsage, get_model

from games.evals import model_player, opening_prompts, play_game
from games.exceptions import FeedbackError
from games.feedback import feedback_path, phase_key, read_feedback, write_note
from games.play import ELIMINATED, HORIZON_REACHED, SOLO, board, dumbbot_seats, opening, play
from games.scoring import share
from select_orders import prompt
from select_orders.prompt_names import game_prompt_digest, prompt_name

FALL_1901 = {"season": "Fall", "year": 1901, "type": "Movement"}
OPENING_MOVE = "lon:Move:nth"


def _state(phase, units, supply_centers):
    return board().game_state(
        phase,
        [{"type": unit_type, "nation": nation, "province": province} for unit_type, nation, province in units],
        [{"nation": nation, "province": province} for nation, province in supply_centers],
    )


def _calls(seen):
    async def turn(here):
        seen.append((here["nation"], here["phase"]["type"]))
        return {"orders": []}

    return turn


def _silent(seen=None):
    seen = [] if seen is None else seen
    return {nation: _calls(seen) for nation in board().nation_ids}


def _game(seed, horizon=1905):
    return asyncio.run(play(dumbbot_seats(seed), "England", horizon=horizon))


def _answer(choices, reasoning="a plan"):
    return json.dumps({"reasoning": reasoning, "choices": [{"option_id": choice} for choice in choices]})


def _output(content):
    output = ModelOutput.from_content("mockllm/model", content)
    output.usage = ModelUsage(input_tokens=10, output_tokens=5, total_tokens=15)
    return output


def _scripted(*contents):
    return get_model("mockllm/model", custom_outputs=[_output(content) for content in contents])


class _FailingModel:
    async def generate(self, messages):
        raise RuntimeError("overloaded")


def _model_turn(model):
    seats = {**_silent(), "England": model_player(model)}
    game = asyncio.run(play(seats, "England", horizon=1901))
    return game["phases"][0]


@pytest.fixture(scope="module")
def full_game():
    return _game(0)


class TestPlay:

    def test_the_same_seed_plays_the_same_game(self):
        assert json.dumps(_game(7, horizon=1902)) == json.dumps(_game(7, horizon=1902))

    def test_another_seed_plays_another_game(self):
        assert _game(7, horizon=1902)["phases"] != _game(8, horizon=1902)["phases"]

    def test_game_starts_at_spring_1901_movement_with_every_nation_ordering(self, full_game):
        first = full_game["phases"][0]
        assert first["phase"] == {"season": "Spring", "year": 1901, "type": "Movement"}
        assert len(first["orders"]) == 7
        assert all(len(orders) == 3 for nation, orders in first["orders"].items() if nation != "Russia")

    def test_game_stops_after_the_fall_1905_retreat_without_the_adjustment(self, full_game):
        assert full_game["end"] == HORIZON_REACHED
        assert full_game["phases"][-1]["phase"] == {"season": "Fall", "year": 1905, "type": "Retreat"}
        assert len(full_game["phases"]) == 24

    def test_phase_with_no_legal_option_is_recorded_without_calling_anyone(self):
        seen = []
        game = asyncio.run(play(_silent(seen), "England", horizon=1901))
        spring_retreat = game["phases"][1]
        assert spring_retreat["phase"]["type"] == "Retreat"
        assert spring_retreat["orders"] == {}
        assert ("England", "Retreat") not in seen

    def test_only_nations_with_legal_options_are_called(self):
        seen = []
        state = _state(FALL_1901, [("Army", "France", "par")], [("France", "par"), ("England", "lon")])
        asyncio.run(play(_silent(seen), "England", state=state, horizon=1901))
        assert seen == [("France", "Movement")]

    def test_final_centres_come_from_the_state_the_fall_1905_adjustment_starts_with(self):
        state = _state(
            {"season": "Fall", "year": 1905, "type": "Movement"},
            [("Army", "England", "bel")],
            [("England", "lon")],
        )
        game = asyncio.run(play(_silent(), "England", state=state))
        assert [center["province"] for center in game["phases"][-1]["supply_centers"]] == ["lon"]
        assert game["centres"]["England"] == 2
        assert game["end"] == HORIZON_REACHED

    def test_game_stops_early_when_the_nation_is_eliminated(self):
        state = _state(FALL_1901, [("Army", "England", "yor")], [("France", "par")])
        game = asyncio.run(play(_silent(), "England", state=state))
        assert game["end"] == ELIMINATED
        assert [phase["phase"]["type"] for phase in game["phases"]] == ["Movement", "Retreat"]
        assert game["centres"]["England"] == 0

    def test_game_stops_early_when_a_nation_solos(self):
        centres = [p["id"] for p in board().variant["provinces"] if p["supplyCenter"] and p["id"] != "lon"][:18]
        state = _state(FALL_1901, [("Army", "England", "lon")], [("England", "lon"), *[("Turkey", c) for c in centres]])
        game = asyncio.run(play(_silent(), "England", state=state))
        assert game["end"] == SOLO
        assert game["centres"]["Turkey"] == 18

    def test_nation_without_orders_holds_its_units(self):
        state = _state(FALL_1901, [("Army", "France", "par")], [("France", "par")])
        game = asyncio.run(play(_silent(), "England", state=state, horizon=1901))
        assert game["phases"][1]["units"] == [{"type": "Army", "nation": "France", "province": "par"}]

    def test_every_order_is_resolved(self, full_game):
        first = full_game["phases"][0]
        ordered = {(nation, order["source"]) for nation, orders in first["orders"].items() for order in orders}
        assert {(entry["nation"], entry["source"]) for entry in first["resolutions"]} == ordered

    def test_later_orders_for_an_ordered_province_are_dropped(self):
        async def twice(here):
            return {
                "orders": [
                    {"source": "par", "order_type": "Move", "target": "bur"},
                    {"source": "par", "order_type": "Hold"},
                ]
            }

        state = _state(FALL_1901, [("Army", "France", "par")], [("France", "par")])
        game = asyncio.run(play({**_silent(), "France": twice}, "England", state=state, horizon=1901))
        assert game["phases"][0]["orders"]["France"] == [{"source": "par", "order_type": "Move", "target": "bur"}]

    def test_opening_has_every_nation_on_its_home_centres(self):
        assert len(opening()["supplyCenters"]) == 22


class TestShare:

    def test_level_board_shares_equally(self):
        centres = {nation: 3 for nation in board().nation_ids}
        assert share(centres, "England", 18) == pytest.approx(100 / 7)

    def test_share_is_normalised_sum_of_squares(self):
        assert share({"England": 4, "France": 2, "Germany": 2}, "England", 18) == pytest.approx(100 * 16 / 24)

    def test_solo_takes_everything(self):
        centres = {"Turkey": 18, "England": 10, "France": 6}
        assert (share(centres, "Turkey", 18), share(centres, "England", 18)) == (100.0, 0.0)

    def test_eliminated_nation_scores_nothing(self):
        assert share({"England": 0, "France": 12, "Germany": 10}, "England", 18) == 0.0


class TestModelPlayer:

    def test_valid_answer_is_applied(self):
        phase = _model_turn(_scripted(_answer([OPENING_MOVE], "go north"), _answer([])))
        assert phase["orders"]["England"] == [{"source": "lon", "order_type": "Move", "target": "nth"}]
        answer = phase["answers"]["England"]
        assert (answer["reasoning"], answer["problem"]) == ("go north", None)
        assert answer["system"].startswith("You are an expert Diplomacy player.")
        assert "You are playing as England." in answer["user"]

    def test_unknown_option_id_fails_the_phase_and_keeps_the_completion(self):
        phase = _model_turn(_scripted(_answer(["lon:Move:mos"]), _answer([])))
        answer = phase["answers"]["England"]
        assert phase["orders"]["England"] == []
        assert answer["problem"] == "unknown option id 'lon:Move:mos'"
        assert "lon:Move:mos" in answer["completion"]

    def test_invalid_json_fails_the_phase_and_keeps_the_completion(self):
        phase = _model_turn(_scripted("I would move to the North Sea", _answer([])))
        answer = phase["answers"]["England"]
        assert phase["orders"]["England"] == []
        assert answer["problem"].startswith("could not parse JSON")
        assert answer["completion"] == "I would move to the North Sea"

    def test_failed_model_call_fails_the_phase(self):
        phase = _model_turn(_FailingModel())
        answer = phase["answers"]["England"]
        assert phase["orders"]["England"] == []
        assert answer["problem"] == "model call failed: overloaded"
        assert answer["completion"] is None

    def test_failed_phase_leaves_the_units_holding(self):
        seats = {**_silent(), "England": model_player(_scripted("not json", _answer([])))}
        game = asyncio.run(play(seats, "England", horizon=1901))
        english = [unit["province"] for unit in game["phases"][2]["units"] if unit["nation"] == "England"]
        assert english == ["edi", "lon", "lvp"]


class TestPlayGame:

    @pytest.fixture(scope="class")
    def logged(self, tmp_path_factory):
        logs_dir = tmp_path_factory.mktemp("logs")
        model = get_model("mockllm/model", custom_outputs=lambda *args, **kwargs: _output(_answer([])))
        digest = game_prompt_digest("England", *opening_prompts("England"))
        (log,) = inspect_eval(
            play_game("England", 3, 1),
            model=model,
            display="none",
            log_dir=str(logs_dir),
            metadata={"prompt": {"name": "calm-lantern-oct-15", "digest": digest}},
        )
        return logs_dir, digest, read_eval_log(log.location)

    def test_sample_is_one_game_carrying_its_whole_trajectory(self, logged):
        _, _, log = logged
        (sample,) = log.samples
        assert (log.eval.task, sample.id, sample.metadata["seed"], sample.metadata["nation"]) == (
            "play_game",
            3,
            3,
            "England",
        )
        phases = sample.store["phases"]
        assert len(phases) == 24
        assert all("England" in phase["answers"] for phase in phases if "England" in phase["orders"])

    def test_sample_records_the_result_and_the_paired_dumbbot_game(self, logged):
        _, _, log = logged
        (sample,) = log.samples
        assert sample.metadata["end"] == HORIZON_REACHED
        assert set(sample.metadata["centres"]) == set(board().nation_ids)
        assert sample.metadata["paired_centres"] == _game(3)["centres"]

    def test_model_calls_are_counted_in_the_log(self, logged):
        _, _, log = logged
        (sample,) = log.samples
        assert sum(usage.input_tokens for usage in sample.model_usage.values()) > 0

    def test_logged_game_prompt_keeps_its_name(self, logged):
        logs_dir, digest, _ = logged
        assert prompt_name(digest, logs_dir, date(2026, 11, 1)) == "calm-lantern-oct-15"


class TestGamePromptDigest:

    def test_digest_is_stable_for_the_same_prompt(self):
        assert game_prompt_digest("England", *opening_prompts("England")) == game_prompt_digest(
            "England", *opening_prompts("England")
        )

    def test_digest_changes_with_a_prompt_part(self, monkeypatch):
        before = game_prompt_digest("England", *opening_prompts("England"))
        monkeypatch.setitem(prompt.DEFAULT_PARTS, "system.role", "You play Diplomacy.")
        assert game_prompt_digest("England", *opening_prompts("England")) != before

    def test_digest_differs_between_nations(self):
        assert game_prompt_digest("England", *opening_prompts("England")) != game_prompt_digest(
            "France", *opening_prompts("France")
        )


class TestPlayGames:

    def test_skips_without_an_api_key(self, monkeypatch, capsys):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        call_command("play_games", nation="England")
        assert "skip: ANTHROPIC_API_KEY is not set" in capsys.readouterr().out

    def test_unknown_nation_is_refused(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "unused")
        with pytest.raises(CommandError):
            call_command("play_games", nation="Atlantis")


class TestDumbbotReference:

    def test_writes_each_seed_result_for_the_nation(self, settings, tmp_path):
        settings.EVALS_REFERENCE_DIR = tmp_path
        call_command("dumbbot_reference", nation="England", seeds=2)
        reference = json.loads((tmp_path / "england.json").read_text())
        expected = [_game(seed) for seed in (0, 1)]
        assert reference["nation"] == "England"
        assert [game["seed"] for game in reference["games"]] == [0, 1]
        assert [game["centres"] for game in reference["games"]] == [game["centres"]["England"] for game in expected]
        assert reference["games"][0]["share"] == pytest.approx(share(expected[0]["centres"], "England", 18))

    def test_unknown_nation_is_refused(self, settings, tmp_path):
        settings.EVALS_REFERENCE_DIR = tmp_path
        with pytest.raises(CommandError):
            call_command("dumbbot_reference", nation="Atlantis", seeds=1)


KEYS = {"1901-Spring-Movement", "1902-Fall-Movement"}


class TestFeedback:

    def _path(self, tmp_path):
        return feedback_path(tmp_path, "run", 0)

    def test_phase_key_names_year_season_and_type(self):
        assert phase_key({"season": "Fall", "year": 1902, "type": "Movement"}) == "1902-Fall-Movement"

    def test_notes_are_written_to_the_game_file(self, tmp_path):
        path = self._path(tmp_path)
        write_note(path, "England", KEYS, "1902-Fall-Movement", "Left Norway open.")
        write_note(path, "England", KEYS, None, "Too passive.")
        assert read_feedback(path) == {
            "nation": "England",
            "overall": "Too passive.",
            "phases": {"1902-Fall-Movement": "Left Norway open."},
        }

    def test_phase_notes_are_kept_in_game_order(self, tmp_path):
        path = self._path(tmp_path)
        write_note(path, "England", KEYS, "1902-Fall-Movement", "later")
        write_note(path, "England", KEYS, "1901-Spring-Movement", "earlier")
        assert list(read_feedback(path)["phases"]) == ["1901-Spring-Movement", "1902-Fall-Movement"]

    def test_phase_the_game_does_not_contain_is_rejected(self, tmp_path):
        with pytest.raises(FeedbackError):
            write_note(self._path(tmp_path), "England", KEYS, "1903-Fall-Movement", "note")
        assert not self._path(tmp_path).exists()

    def test_empty_note_is_removed(self, tmp_path):
        path = self._path(tmp_path)
        write_note(path, "England", KEYS, None, "Too passive.")
        write_note(path, "England", KEYS, "1902-Fall-Movement", "Left Norway open.")
        write_note(path, "England", KEYS, "1902-Fall-Movement", "  ")
        assert read_feedback(path) == {"nation": "England", "overall": "Too passive."}

    def test_file_with_no_note_left_is_deleted(self, tmp_path):
        path = self._path(tmp_path)
        write_note(path, "England", KEYS, "1902-Fall-Movement", "Left Norway open.")
        write_note(path, "England", KEYS, "1902-Fall-Movement", "")
        assert not path.exists()
        assert not path.parent.exists()

    def test_unknown_key_in_a_file_is_rejected(self, tmp_path):
        path = self._path(tmp_path)
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"nation": "England", "verdict": "bad"}))
        with pytest.raises(FeedbackError):
            read_feedback(path)

    def test_malformed_phase_key_in_a_file_is_rejected(self, tmp_path):
        path = self._path(tmp_path)
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"nation": "England", "phases": {"autumn": "note"}}))
        with pytest.raises(FeedbackError):
            read_feedback(path)

    def test_note_for_another_nation_is_rejected(self, tmp_path):
        path = self._path(tmp_path)
        write_note(path, "England", KEYS, None, "Too passive.")
        with pytest.raises(FeedbackError):
            write_note(path, "France", KEYS, None, "Too bold.")
