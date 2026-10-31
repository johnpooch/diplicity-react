from functools import cache
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from inspect_ai.log import read_eval_log, read_eval_log_sample

from prompt_builder import own_units_first
from prompt_builder.variants import VARIANTS
from select_orders.context import fixture_to_context
from select_orders.evals import fixture_to_sample, load_fixtures, select_fixtures
from select_orders.exceptions import PromptError

P2_ENGLAND = "gunboat-12hr-classic_p2_england"
OPENING = "opening"


def _context(fixture_id):
    [fixture] = select_fixtures(None, fixture_id)
    return fixture_to_context(fixture)


def _spring_1901():
    return [
        fixture
        for fixture in load_fixtures(OPENING)
        if (
            fixture["phase"]["season"],
            fixture["phase"]["year"],
            fixture["phase"]["type"],
        )
        == ("Spring", 1901, "Movement")
    ]


@cache
def _logged_user_prompts():
    prompts = {}
    for path in sorted(Path(settings.EVALS_LOGS_DIR).glob("*.eval")):
        header = read_eval_log(str(path), header_only=True)
        args = header.eval.task_args or {}
        variant = Path(args.get("user_file") or "").stem
        if args.get("fixture_id") == P2_ENGLAND and variant in VARIANTS:
            sample = read_eval_log_sample(str(path), id=P2_ENGLAND, epoch=1)
            prompts[variant] = next(
                message.text for message in sample.input if message.role == "user"
            )
    return prompts


class TestVariants:

    @pytest.mark.parametrize("variant", sorted(VARIANTS))
    def test_reproduces_the_prompt_its_england_p2_run_sent(self, variant):
        logged = _logged_user_prompts()
        assert f"{VARIANTS[variant](_context(P2_ENGLAND))}\n" == logged[variant]

    @pytest.mark.parametrize("variant", sorted(VARIANTS))
    def test_every_spring_1901_prompt_lists_every_option(self, variant):
        fixtures = _spring_1901()
        assert len(fixtures) == 7
        for fixture in fixtures:
            fixture_to_sample(
                fixture, user=VARIANTS[variant](fixture_to_context(fixture))
            )

    def test_fleet_on_a_named_coast_moves_from_that_coast(self):
        text = own_units_first.build(_context("russia_spring_1901"))
        fleet = text.split("  Fleet St. Petersburg (SC) (stp/sc)\n")[1].split(
            "\n  Army"
        )[0]
        assert [line.split(" [")[0].strip() for line in fleet.splitlines()[1:]] == [
            "Gulf of Bothnia (bot)",
            "Finland (fin)",
            "Livonia (lvn)",
        ]

    def test_refuses_a_phase_other_than_movement(self):
        with pytest.raises(PromptError):
            own_units_first.build(_context("retreat_to_supply_center"))


class TestBuildPrompts:

    def _build(self, out, **options):
        call_command("build_prompts", eval_set=OPENING, out=str(out), **options)

    def test_writes_each_variant_for_each_fixture(self, tmp_path):
        self._build(tmp_path, season="Spring", year=1901)
        written = sorted(
            path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*.txt")
        )
        expected = sorted(
            f"{fixture['id']}/{variant}.txt"
            for fixture in _spring_1901()
            for variant in VARIANTS
        )
        assert written == expected

    def test_written_prompt_is_the_variant_text(self, tmp_path):
        self._build(
            tmp_path, fixture="england_spring_1901", variant=["user_2_contest_table"]
        )
        text = (
            tmp_path / "england_spring_1901" / "user_2_contest_table.txt"
        ).read_text()
        assert (
            text
            == f"{VARIANTS['user_2_contest_table'](_context('england_spring_1901'))}\n"
        )

    def test_rebuilding_leaves_an_unchanged_prompt(self, tmp_path):
        self._build(
            tmp_path, fixture="england_spring_1901", variant=["user_5_distance_rings"]
        )
        self._build(
            tmp_path, fixture="england_spring_1901", variant=["user_5_distance_rings"]
        )

    def test_refuses_to_overwrite_an_edited_prompt(self, tmp_path):
        self._build(
            tmp_path, fixture="england_spring_1901", variant=["user_5_distance_rings"]
        )
        path = tmp_path / "england_spring_1901" / "user_5_distance_rings.txt"
        path.write_text(path.read_text() + "Think carefully.\n")
        with pytest.raises(CommandError):
            self._build(
                tmp_path,
                fixture="england_spring_1901",
                variant=["user_5_distance_rings"],
            )

    def test_no_matching_fixture_raises(self, tmp_path):
        with pytest.raises(CommandError):
            self._build(tmp_path, season="Winter")
