import copy
import json

import pytest
from django.core.management import CommandError, call_command

from engine.rules import load_variant
from harvest.build import Harvest
from harvest.exceptions import HarvestError
from harvest.snapshot import validate_snapshot
from select_orders.fixtures import read_fixture, validate_fixture

GAME = "harvested-game-1a2b3c4d"
SPRING = 101
FALL = 102
NATIONS = ["Austria", "England", "France", "Germany", "Italy", "Russia", "Turkey"]


def _opening_units(phase, moved=None):
    variant = load_variant("classical")
    names = {nation["id"]: nation["name"] for nation in variant["nations"]}
    moved = moved or {}
    return [
        {
            "phase": phase,
            "province": moved.get(unit["location"], unit["location"]),
            "type": unit["type"],
            "nation": names[unit["nation"]],
            "dislodged": False,
            "dislodged_from": None,
        }
        for unit in variant["initialState"]["units"]
    ]


def _opening_supply_centers(phase):
    variant = load_variant("classical")
    names = {nation["id"]: nation["name"] for nation in variant["nations"]}
    return [
        {"phase": phase, "province": center["province"], "nation": names[center["nation"]]}
        for center in variant["initialState"]["supplyCenters"]
    ]


def _order(nation, source, order_type, target=None, resolution="OK", **fields):
    return {
        "phase": SPRING,
        "nation": nation,
        "order_type": order_type,
        "source": source,
        "target": target,
        "aux": fields.get("aux"),
        "unit_type": fields.get("unit_type"),
        "named_coast": fields.get("named_coast"),
        "resolution": resolution,
    }


def _phase(phase_id, ordinal, season, status):
    return {
        "id": phase_id,
        "game": GAME,
        "ordinal": ordinal,
        "season": season,
        "year": 1901,
        "type": "Movement",
        "status": status,
        "contested_provinces": [],
    }


def _snapshot():
    return {
        "games": [{"id": GAME, "variant": "classical", "press_type": "full_press", "status": "active"}],
        "phases": [_phase(SPRING, 1, "Spring", "completed"), _phase(FALL, 2, "Fall", "active")],
        "units": _opening_units(SPRING) + _opening_units(FALL, moved={"lon": "eng", "bud": "gal"}),
        "supply_centers": _opening_supply_centers(SPRING) + _opening_supply_centers(FALL),
        "orders": [
            _order("England", "lon", "Move", "eng"),
            _order("France", "par", "Move", "bur", resolution="ErrBounce"),
            _order("Germany", "mun", "Move", "bur", resolution="ErrBounce"),
            _order("Austria", "bud", "Move", "gal"),
            _order("Austria", "vie", "Support", "gal", aux="bud"),
            _order("Russia", "war", "Move", "gal", resolution="ErrBounce"),
        ],
        "players": [{"phase": SPRING, "nation": nation, "was_bot": nation == "Germany"} for nation in NATIONS],
    }


def _adjustment_snapshot():
    snapshot = _snapshot()
    snapshot["phases"] = [{**_phase(SPRING, 1, "Fall", "completed"), "type": "Adjustment"}]
    snapshot["units"] = [unit for unit in _opening_units(SPRING) if unit["province"] != "lon"]
    snapshot["orders"] = [_order("England", "lon", "Build", unit_type="Army")]
    return snapshot


def _harvest(snapshot=None):
    return Harvest(validate_snapshot(snapshot or _snapshot()), harvested_at="2026-09-28T12:00:00+00:00")


def _fixture(nation, snapshot=None):
    return next(fixture for fixture in _harvest(snapshot).fixtures(SPRING) if fixture["nation"] == nation)


class TestHarvest:

    def test_builds_a_fixture_with_legal_options_for_every_nation_in_a_past_phase(self):
        fixtures = _harvest().fixtures(SPRING)
        assert [fixture["nation"] for fixture in fixtures] == NATIONS
        assert all(fixture["order_options"] for fixture in fixtures)

    def test_every_fixture_validates_against_the_schema(self):
        for fixture in _harvest().fixtures(SPRING):
            assert validate_fixture(fixture) == fixture

    def test_new_fixture_is_in_no_eval_set(self):
        assert _fixture("England")["eval_sets"] == []

    def test_provenance_records_the_source_phase_and_whether_a_bot_played_it(self):
        assert _fixture("Germany")["provenance"] == {
            "source": "harvested",
            "game_id": GAME,
            "phase_id": SPRING,
            "phase_ordinal": 1,
            "harvested_at": "2026-09-28T12:00:00+00:00",
            "press_type": "full_press",
            "was_bot": True,
        }

    def test_actual_orders_cover_every_nation_with_units(self):
        actual = _fixture("England")["actual_orders"]
        assert sorted(actual) == NATIONS
        assert actual["Italy"] == []
        assert actual["Austria"] == [
            {"source": "bud", "order_type": "Move", "target": "gal"},
            {"source": "vie", "order_type": "Support", "target": "gal", "aux": "bud"},
        ]

    def test_actual_orders_are_drawn_from_the_legal_options(self):
        fixture = _fixture("Austria")
        assert all(order in fixture["order_options"] for order in fixture["actual_orders"]["Austria"])

    def test_actual_outcome_records_each_order_result_and_the_resulting_board(self):
        outcome = _fixture("England")["actual_outcome"]
        assert {"nation": "France", "source": "par", "result": "ErrBounce"} in outcome["resolutions"]
        assert {"nation": "Russia", "source": "war", "result": "ErrBounce"} in outcome["resolutions"]
        assert {"nation": "Austria", "source": "vie", "result": "OK"} in outcome["resolutions"]
        provinces = {unit["province"] for unit in outcome["units"]}
        assert {"eng", "gal", "war"} <= provinces and not {"lon", "bud", "bur"} & provinces

    def test_decision_richness_is_the_product_of_per_unit_option_counts(self):
        fixture = _fixture("Turkey")
        counts = {}
        for option in fixture["order_options"]:
            counts[option["source"]] = counts.get(option["source"], 0) + 1
        assert len(counts) == 3
        assert fixture["decision_richness"] == counts["ank"] * counts["con"] * counts["smy"]

    def test_options_for_a_past_phase_match_the_same_board_as_the_current_phase(self):
        current = _snapshot()
        current["phases"] = [{**current["phases"][0], "status": "active"}]
        current["units"] = [unit for unit in current["units"] if unit["phase"] == SPRING]
        current["supply_centers"] = [center for center in current["supply_centers"] if center["phase"] == SPRING]
        current["orders"] = []
        assert _harvest().legal_options(SPRING) == _harvest(current).legal_options(SPRING)

    def test_adjustment_fixture_limits_orders_to_the_build_count(self):
        fixture = _fixture("England", _adjustment_snapshot())
        assert fixture["max_orders"] == 1
        assert fixture["actual_orders"]["England"] == [{"source": "lon", "order_type": "Build", "unit_type": "Army"}]

    def test_unfinished_phase_is_not_harvested(self):
        with pytest.raises(HarvestError):
            _harvest().fixtures(FALL)

    def test_unknown_phase_is_rejected(self):
        with pytest.raises(HarvestError):
            _harvest().fixtures(999)

    def test_unknown_variant_is_rejected(self):
        snapshot = _snapshot()
        snapshot["games"][0]["variant"] = "hundred"
        with pytest.raises(HarvestError):
            _harvest(snapshot).fixtures(SPRING)

    def test_order_that_is_not_a_legal_option_is_rejected(self):
        snapshot = _snapshot()
        snapshot["orders"].append(_order("Italy", "ven", "Move", "mun"))
        with pytest.raises(HarvestError):
            _harvest(snapshot).fixtures(SPRING)

    def test_stored_resolution_that_disagrees_with_the_replay_is_rejected(self):
        snapshot = _snapshot()
        snapshot["orders"][1]["resolution"] = "OK"
        with pytest.raises(HarvestError):
            _harvest(snapshot).fixtures(SPRING)

    def test_stored_failure_reported_under_another_code_is_accepted(self):
        snapshot = _snapshot()
        snapshot["orders"][1]["resolution"] = "ErrIllegalMove"
        outcome = next(f for f in _harvest(snapshot).fixtures(SPRING) if f["nation"] == "France")["actual_outcome"]
        assert {"nation": "France", "source": "par", "result": "ErrBounce"} in outcome["resolutions"]

    def test_next_stored_phase_that_disagrees_with_the_replay_is_rejected(self):
        snapshot = _snapshot()
        moved = next(unit for unit in snapshot["units"] if unit["phase"] == FALL and unit["province"] == "par")
        moved["province"] = "bur"
        with pytest.raises(HarvestError):
            _harvest(snapshot).fixtures(SPRING)


class TestSnapshot:

    @pytest.mark.parametrize("table", ["games", "phases", "units", "supply_centers", "orders", "players"])
    def test_user_identifier_is_rejected(self, table):
        snapshot = _snapshot()
        snapshot[table][0]["user_id"] = 42
        with pytest.raises(HarvestError):
            validate_snapshot(snapshot)

    def test_extra_table_is_rejected(self):
        with pytest.raises(HarvestError):
            validate_snapshot({**_snapshot(), "members": []})


class TestBuildFixturesCommand:

    def _snapshot_path(self, tmp_path, snapshot=None):
        path = tmp_path / "snapshot.json"
        path.write_text(json.dumps(snapshot or _snapshot()))
        return path

    def test_writes_one_fixture_per_nation_for_each_completed_phase(self, tmp_path):
        out = tmp_path / "fixtures"
        call_command("build_fixtures", str(self._snapshot_path(tmp_path)), "--out", str(out))
        assert sorted(path.name for path in out.iterdir()) == [f"{GAME}_p1_{nation.lower()}.json" for nation in NATIONS]
        assert read_fixture(out / f"{GAME}_p1_england.json")["nation"] == "England"

    def test_nation_filter_limits_the_eval_nations(self, tmp_path):
        out = tmp_path / "fixtures"
        call_command("build_fixtures", str(self._snapshot_path(tmp_path)), "--out", str(out), "--nation", "France")
        assert [path.name for path in out.iterdir()] == [f"{GAME}_p1_france.json"]

    def test_existing_fixture_is_left_untouched(self, tmp_path):
        out = tmp_path / "fixtures"
        snapshot_path = self._snapshot_path(tmp_path)
        call_command("build_fixtures", str(snapshot_path), "--out", str(out))
        path = out / f"{GAME}_p1_england.json"
        labelled = {**json.loads(path.read_text()), "eval_sets": ["dev"]}
        path.write_text(json.dumps(labelled))
        call_command("build_fixtures", str(snapshot_path), "--out", str(out))
        assert json.loads(path.read_text())["eval_sets"] == ["dev"]

    def test_phase_that_fails_is_skipped_and_the_rest_are_written(self, tmp_path):
        snapshot = copy.deepcopy(_snapshot())
        snapshot["orders"][1]["resolution"] = "OK"
        out = tmp_path / "fixtures"
        call_command("build_fixtures", str(self._snapshot_path(tmp_path, snapshot)), "--out", str(out))
        assert list(out.iterdir()) == []

    def test_missing_snapshot_is_an_error(self, tmp_path):
        with pytest.raises(CommandError):
            call_command("build_fixtures", str(tmp_path / "missing.json"))
