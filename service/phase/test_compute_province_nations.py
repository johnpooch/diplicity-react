import pytest
from unittest.mock import MagicMock
from phase.utils import compute_province_nations
from common.constants import ProvinceType


def _make_province(province_id, ptype, supply_center=False, parent=None, adjacencies=None):
    p = MagicMock()
    p.province_id = province_id
    p.type = ptype
    p.supply_center = supply_center
    p.parent = parent
    p.parent_id = parent.pk if parent else None
    p.adjacencies = adjacencies or []
    return p


def _make_nation(nation_id, name):
    n = MagicMock()
    n.nation_id = nation_id
    n.name = name
    return n


def _make_sc(province_id, nation_name, province_obj, nation_obj):
    sc = MagicMock()
    sc.province = province_obj
    sc.nation = nation_obj
    return sc


class TestComputeProvinceNations:

    def test_returns_empty_dict_when_no_non_sc_provinces(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        sc = _make_sc("lon", "England", sc_province, nation)

        result = compute_province_nations([sc], [sc_province], [], [nation])

        assert result == {}

    def test_excludes_sea_provinces(self):
        sea_province = _make_province("nth", ProvinceType.SEA)
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True, adjacencies=[{"to": "nth"}])
        nation = _make_nation("england", "England")
        sc = _make_sc("lon", "England", sc_province, nation)

        result = compute_province_nations([sc], [sea_province, sc_province], [], [nation])

        assert "nth" not in result

    def test_excludes_named_coast_provinces(self):
        parent = _make_province("spa", ProvinceType.COASTAL, supply_center=True)
        parent.pk = 1
        named_coast = _make_province("spa/nc", ProvinceType.NAMED_COAST, parent=parent)
        nation = _make_nation("france", "France")
        sc = _make_sc("spa", "France", parent, nation)

        result = compute_province_nations([sc], [named_coast, parent], [], [nation])

        assert "spa/nc" not in result

    def test_excludes_supply_center_provinces(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        sc = _make_sc("lon", "England", sc_province, nation)
        non_sc = _make_province("wal", ProvinceType.COASTAL, adjacencies=[{"to": "lon"}])

        result = compute_province_nations([sc], [sc_province, non_sc], [], [nation])

        assert "lon" not in result

    def test_default_color_single_adjacent_owned_sc(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        sc = _make_sc("lon", "England", sc_province, nation)
        non_sc = _make_province("wal", ProvinceType.COASTAL, adjacencies=[{"to": "lon"}])

        result = compute_province_nations([sc], [sc_province, non_sc], [], [nation])

        assert result["wal"] == "England"

    def test_default_color_multiple_adjacent_same_owner(self):
        sc1 = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        sc2 = _make_province("edi", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        sc_obj1 = _make_sc("lon", "England", sc1, nation)
        sc_obj2 = _make_sc("edi", "England", sc2, nation)
        non_sc = _make_province("wal", ProvinceType.COASTAL, adjacencies=[{"to": "lon"}, {"to": "edi"}])

        result = compute_province_nations([sc_obj1, sc_obj2], [sc1, sc2, non_sc], [], [nation])

        assert result["wal"] == "England"

    def test_default_color_adjacent_to_multiple_owners_returns_no_color(self):
        sc1 = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        sc2 = _make_province("par", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        france = _make_nation("france", "France")
        sc_obj1 = _make_sc("lon", "England", sc1, england)
        sc_obj2 = _make_sc("par", "France", sc2, france)
        non_sc = _make_province("pic", ProvinceType.COASTAL, adjacencies=[{"to": "lon"}, {"to": "par"}])

        result = compute_province_nations([sc_obj1, sc_obj2], [sc1, sc2, non_sc], [], [england, france])

        assert "pic" not in result

    def test_default_color_no_adjacent_sc_returns_no_color(self):
        non_sc1 = _make_province("bur", ProvinceType.LAND, adjacencies=[{"to": "mun"}])
        non_sc2 = _make_province("mun", ProvinceType.COASTAL, adjacencies=[{"to": "bur"}])
        england = _make_nation("england", "England")

        result = compute_province_nations([], [non_sc1, non_sc2], [], [england])

        assert "bur" not in result
        assert "mun" not in result

    def test_default_color_adjacent_unowned_sc_returns_no_color(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        non_sc = _make_province("wal", ProvinceType.COASTAL, adjacencies=[{"to": "lon"}])

        result = compute_province_nations([], [sc_province, non_sc], [], [nation])

        assert "wal" not in result

    def test_dominance_rule_matched_overrides_default(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        sc_province2 = _make_province("par", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        france = _make_nation("france", "France")
        sc_obj1 = _make_sc("lon", "England", sc_province, england)
        sc_obj2 = _make_sc("par", "France", sc_province2, france)
        non_sc = _make_province("pic", ProvinceType.LAND, adjacencies=[{"to": "lon"}, {"to": "par"}])

        dominance_rules = [
            {
                "province": "pic",
                "nation": "england",
                "dependencies": [{"province": "lon", "nation": "england"}],
            }
        ]

        result = compute_province_nations(
            [sc_obj1, sc_obj2], [sc_province, sc_province2, non_sc], dominance_rules, [england, france]
        )

        assert result["pic"] == "England"

    def test_dominance_rule_not_matched_falls_through_to_default(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        sc_province2 = _make_province("par", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        france = _make_nation("france", "France")
        sc_obj1 = _make_sc("lon", "England", sc_province, england)
        sc_obj2 = _make_sc("par", "France", sc_province2, france)
        non_sc = _make_province("pic", ProvinceType.LAND, adjacencies=[{"to": "lon"}, {"to": "par"}])

        dominance_rules = [
            {
                "province": "pic",
                "nation": "england",
                "dependencies": [{"province": "lon", "nation": "france"}],
            }
        ]

        result = compute_province_nations(
            [sc_obj1, sc_obj2], [sc_province, sc_province2, non_sc], dominance_rules, [england, france]
        )

        assert "pic" not in result

    def test_dominance_rule_not_matched_falls_through_to_default_color(self):
        # Gascony case: rule requires spa=Empty, but spa is owned by France.
        # Rule fails → should fall back to adjacency logic (all adjacent SCs are France).
        spa = _make_province("spa", ProvinceType.COASTAL, supply_center=True)
        bre = _make_province("bre", ProvinceType.COASTAL, supply_center=True)
        france = _make_nation("france", "France")
        sc_spa = _make_sc("spa", "France", spa, france)
        sc_bre = _make_sc("bre", "France", bre, france)
        gas = _make_province("gas", ProvinceType.LAND, adjacencies=[{"to": "spa"}, {"to": "bre"}])

        dominance_rules = [
            {
                "province": "gas",
                "nation": "france",
                "dependencies": [{"province": "spa", "nation": "Empty"}],
            }
        ]

        result = compute_province_nations(
            [sc_spa, sc_bre], [spa, bre, gas], dominance_rules, [france]
        )

        assert result.get("gas") == "France"

    def test_dominance_rule_with_empty_dependency_always_matches(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        sc_obj = _make_sc("lon", "England", sc_province, england)
        non_sc = _make_province("bur", ProvinceType.LAND, adjacencies=[])

        dominance_rules = [
            {
                "province": "bur",
                "nation": "england",
                "dependencies": [],
            }
        ]

        result = compute_province_nations([sc_obj], [sc_province, non_sc], dominance_rules, [england])

        assert result["bur"] == "England"

    def test_dominance_rule_neutral_marker_matches_unowned_sc(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        non_sc = _make_province("bur", ProvinceType.LAND, adjacencies=[{"to": "lon"}])

        dominance_rules = [
            {
                "province": "bur",
                "nation": "england",
                "dependencies": [{"province": "lon", "nation": "Neutral"}],
            }
        ]

        result = compute_province_nations([], [sc_province, non_sc], dominance_rules, [england])

        assert result["bur"] == "England"

    def test_dominance_rule_neutral_marker_does_not_match_owned_sc(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        sc_obj = _make_sc("lon", "England", sc_province, england)
        non_sc = _make_province("bur", ProvinceType.LAND, adjacencies=[])

        dominance_rules = [
            {
                "province": "bur",
                "nation": "england",
                "dependencies": [{"province": "lon", "nation": "Neutral"}],
            }
        ]

        result = compute_province_nations([sc_obj], [sc_province, non_sc], dominance_rules, [england])

        assert "bur" not in result

    def test_dominance_rule_empty_marker_matches_unowned_sc(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        non_sc = _make_province("bur", ProvinceType.LAND, adjacencies=[])

        dominance_rules = [
            {
                "province": "bur",
                "nation": "england",
                "dependencies": [{"province": "lon", "nation": "Empty"}],
            }
        ]

        result = compute_province_nations([], [sc_province, non_sc], dominance_rules, [england])

        assert result["bur"] == "England"

    def test_dominance_rule_unknown_nation_id_excluded(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        sc_obj = _make_sc("lon", "England", sc_province, england)
        non_sc = _make_province("bur", ProvinceType.LAND, adjacencies=[])

        dominance_rules = [
            {
                "province": "bur",
                "nation": "unknown_nation",
                "dependencies": [],
            }
        ]

        result = compute_province_nations([sc_obj], [sc_province, non_sc], dominance_rules, [england])

        assert "bur" not in result

    def test_dominance_rule_with_province_has_no_more_rules_after_match(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        sc_province2 = _make_province("par", ProvinceType.COASTAL, supply_center=True)
        england = _make_nation("england", "England")
        france = _make_nation("france", "France")
        sc_obj1 = _make_sc("lon", "England", sc_province, england)
        sc_obj2 = _make_sc("par", "France", sc_province2, france)
        non_sc = _make_province("pic", ProvinceType.LAND, adjacencies=[{"to": "lon"}])

        dominance_rules = [
            {
                "province": "pic",
                "nation": "england",
                "dependencies": [{"province": "lon", "nation": "england"}],
            },
            {
                "province": "pic",
                "nation": "france",
                "dependencies": [{"province": "par", "nation": "france"}],
            },
        ]

        result = compute_province_nations(
            [sc_obj1, sc_obj2], [sc_province, sc_province2, non_sc], dominance_rules, [england, france]
        )

        assert result["pic"] == "England"

    def test_land_province_included(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        sc_obj = _make_sc("lon", "England", sc_province, nation)
        land = _make_province("wal", ProvinceType.LAND, adjacencies=[{"to": "lon"}])

        result = compute_province_nations([sc_obj], [sc_province, land], [], [nation])

        assert result["wal"] == "England"

    def test_coastal_non_sc_province_included(self):
        sc_province = _make_province("lon", ProvinceType.COASTAL, supply_center=True)
        nation = _make_nation("england", "England")
        sc_obj = _make_sc("lon", "England", sc_province, nation)
        coastal = _make_province("yor", ProvinceType.COASTAL, adjacencies=[{"to": "lon"}])

        result = compute_province_nations([sc_obj], [sc_province, coastal], [], [nation])

        assert result["yor"] == "England"

    def test_adjacency_to_named_coast_resolves_via_parent(self):
        parent_sc = _make_province("spa", ProvinceType.COASTAL, supply_center=True)
        parent_sc.pk = 1
        named_coast = _make_province("spa/nc", ProvinceType.NAMED_COAST, parent=parent_sc)
        nation = _make_nation("france", "France")
        sc_obj = _make_sc("spa", "France", parent_sc, nation)
        non_sc = _make_province("gas", ProvinceType.COASTAL, adjacencies=[{"to": "spa/nc"}])

        result = compute_province_nations(
            [sc_obj], [parent_sc, named_coast, non_sc], [], [nation]
        )

        assert result["gas"] == "France"

    def test_empty_inputs_return_empty_dict(self):
        result = compute_province_nations([], [], [], [])
        assert result == {}
