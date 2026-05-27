import copy

import pytest

from common.constants import VariantStatus
from game.models import Game
from nation.models import Nation, NationFlag
from phase.models import Phase
from province.models import Province
from supply_center.models import SupplyCenter
from unit.models import Unit
from variant.models import Variant, VariantSvg
from variant.utils import (
    apply_safe_replacement,
    create_variant_from_dvar,
    validate_safe_replacement,
    variant_to_canonical_dict,
)


@pytest.fixture
def published_variant(db, classical_variant, primary_user):
    base_dvar = variant_to_canonical_dict(classical_variant)
    base_dvar["id"] = "safe-replace-test"
    dvar = copy.deepcopy(base_dvar)
    variant = create_variant_from_dvar(dvar, owner=primary_user, status=VariantStatus.PUBLISHED)
    VariantSvg.objects.create(variant=variant, svg=classical_variant.svg.svg)
    return variant


@pytest.fixture
def published_variant_dvar(published_variant):
    return variant_to_canonical_dict(published_variant)


@pytest.fixture
def published_variant_dsvg(published_variant):
    return published_variant.svg.svg


@pytest.fixture
def sandbox_game_on_published(primary_user, published_variant):
    return Game.objects.create_sandbox(
        user=primary_user, name="Safe replace sandbox", variant=published_variant
    )


def _error_codes(errors):
    return [error.code for error in errors]


@pytest.mark.django_db
def test_validate_accepts_identical_dvar(published_variant, published_variant_dvar):
    errors = validate_safe_replacement(published_variant, published_variant_dvar)
    assert errors == []


@pytest.mark.django_db
def test_validate_rejects_mismatched_id(published_variant, published_variant_dvar):
    bad = copy.deepcopy(published_variant_dvar)
    bad["id"] = "different-id"
    errors = validate_safe_replacement(published_variant, bad)
    assert "VARIANT_ID_MISMATCH" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_rejects_added_nation(published_variant, published_variant_dvar):
    bad = copy.deepcopy(published_variant_dvar)
    bad["nations"].append({"id": "atlantis", "name": "Atlantis", "color": "#abcdef"})
    errors = validate_safe_replacement(published_variant, bad)
    assert "NATION_ADDED" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_rejects_removed_nation(published_variant, published_variant_dvar):
    bad = copy.deepcopy(published_variant_dvar)
    removed_id = bad["nations"][0]["id"]
    surviving_id = bad["nations"][1]["id"]
    bad["nations"] = [nation for nation in bad["nations"] if nation["id"] != removed_id]
    for province in bad["provinces"]:
        if province.get("homeNation") == removed_id:
            province.pop("homeNation", None)
    for unit in bad["initialState"]["units"]:
        if unit["nation"] == removed_id:
            unit["nation"] = surviving_id
    for sc in bad["initialState"]["supplyCenters"]:
        if sc["nation"] == removed_id:
            sc["nation"] = surviving_id
    errors = validate_safe_replacement(published_variant, bad)
    assert "NATION_REMOVED" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_rejects_added_province(published_variant, published_variant_dvar):
    bad = copy.deepcopy(published_variant_dvar)
    bad["provinces"].append(
        {
            "id": "atl",
            "name": "Atlantis",
            "type": "sea",
            "supplyCenter": False,
            "adjacencies": [],
        }
    )
    errors = validate_safe_replacement(published_variant, bad)
    assert "PROVINCE_ADDED" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_rejects_removed_province(published_variant, published_variant_dvar):
    bad = copy.deepcopy(published_variant_dvar)
    removed_id = next(
        province["id"] for province in bad["provinces"]
        if province["type"] == "sea" and not province["supplyCenter"]
    )
    bad["provinces"] = [
        province for province in bad["provinces"] if province["id"] != removed_id
    ]
    for province in bad["provinces"]:
        province["adjacencies"] = [
            adjacency for adjacency in province.get("adjacencies", [])
            if adjacency["to"] != removed_id
        ]
    errors = validate_safe_replacement(published_variant, bad)
    assert "PROVINCE_REMOVED" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_rejects_supply_center_removal_when_active_sc_exists(
    published_variant, published_variant_dvar, sandbox_game_on_published
):
    sc_province_id = (
        SupplyCenter.objects.filter(phase__game=sandbox_game_on_published)
        .first()
        .province.province_id
    )
    bad = copy.deepcopy(published_variant_dvar)
    for province in bad["provinces"]:
        if province["id"] == sc_province_id:
            province["supplyCenter"] = False
            break
    errors = validate_safe_replacement(published_variant, bad)
    assert "SUPPLY_CENTER_REMOVED" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_rejects_parent_change_when_units_exist(
    published_variant, published_variant_dvar, sandbox_game_on_published
):
    template_named_coast = (
        published_variant.provinces.filter(parent__isnull=False).first()
    )
    assert template_named_coast is not None
    Unit.objects.filter(phase__game=sandbox_game_on_published).first()
    unit = Unit.objects.filter(phase__game=sandbox_game_on_published).first()
    unit.province = template_named_coast
    unit.save()

    new_parent_province = (
        published_variant.provinces.exclude(province_id=template_named_coast.parent.province_id)
        .filter(parent__isnull=True)
        .first()
    )
    bad = copy.deepcopy(published_variant_dvar)
    for coast in bad["namedCoasts"]:
        if coast["id"] == template_named_coast.province_id:
            coast["parentProvince"] = new_parent_province.province_id
            break
    errors = validate_safe_replacement(published_variant, bad)
    assert "PARENT_CHANGED" in _error_codes(errors)


@pytest.mark.django_db
def test_validate_accepts_adjacency_change(
    published_variant, published_variant_dvar, sandbox_game_on_published
):
    modified = copy.deepcopy(published_variant_dvar)
    for province in modified["provinces"]:
        if province["adjacencies"]:
            province["adjacencies"] = province["adjacencies"][:-1]
            break
    errors = validate_safe_replacement(published_variant, modified)
    adjacency_errors = [
        error for error in errors
        if error.code in ("ASYMMETRIC_ADJACENCY", "INCONSISTENT_ADJACENCY")
    ]
    nation_or_province_errors = [
        error for error in errors
        if error.code in (
            "NATION_ADDED", "NATION_REMOVED", "PROVINCE_ADDED", "PROVINCE_REMOVED",
            "PARENT_CHANGED", "SUPPLY_CENTER_REMOVED",
        )
    ]
    assert nation_or_province_errors == []
    assert adjacency_errors


@pytest.mark.django_db
def test_apply_preserves_pks(
    published_variant, published_variant_dvar, published_variant_dsvg
):
    nation_pks_before = dict(published_variant.nations.values_list("nation_id", "id"))
    province_pks_before = dict(published_variant.provinces.values_list("province_id", "id"))

    apply_safe_replacement(published_variant, published_variant_dvar, published_variant_dsvg)

    nation_pks_after = dict(
        Nation.objects.filter(variant=published_variant).values_list("nation_id", "id")
    )
    province_pks_after = dict(
        Province.objects.filter(variant=published_variant).values_list("province_id", "id")
    )
    assert nation_pks_after == nation_pks_before
    assert province_pks_after == province_pks_before


@pytest.mark.django_db
def test_apply_preserves_game_data(
    published_variant, published_variant_dvar, published_variant_dsvg,
    sandbox_game_on_published,
):
    game = sandbox_game_on_published
    game_phase_ids = list(game.phases.values_list("id", flat=True))
    unit_ids = list(Unit.objects.filter(phase__game=game).values_list("id", flat=True))
    sc_ids = list(SupplyCenter.objects.filter(phase__game=game).values_list("id", flat=True))
    member_ids = list(game.members.values_list("id", flat=True))

    apply_safe_replacement(published_variant, published_variant_dvar, published_variant_dsvg)

    assert list(game.phases.values_list("id", flat=True)) == game_phase_ids
    assert list(Unit.objects.filter(phase__game=game).values_list("id", flat=True)) == unit_ids
    assert list(SupplyCenter.objects.filter(phase__game=game).values_list("id", flat=True)) == sc_ids
    assert list(game.members.values_list("id", flat=True)) == member_ids


@pytest.mark.django_db
def test_apply_regenerates_template_phase(
    published_variant, published_variant_dvar, published_variant_dsvg
):
    template_phase_id_before = published_variant.template_phase.id
    apply_safe_replacement(published_variant, published_variant_dvar, published_variant_dsvg)
    refreshed_template = Phase.objects.get(
        variant=published_variant, game__isnull=True
    )
    assert refreshed_template.id != template_phase_id_before
    assert refreshed_template.units.exists()
    assert refreshed_template.supply_centers.exists()


@pytest.mark.django_db
def test_apply_preserves_flags(
    published_variant, published_variant_dvar, published_variant_dsvg
):
    nation = published_variant.nations.first()
    flag_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
    NationFlag.objects.create(nation=nation, svg=flag_svg)
    flag_hash_before = nation.flag.content_hash

    apply_safe_replacement(published_variant, published_variant_dvar, published_variant_dsvg)

    refreshed_flag = NationFlag.objects.get(nation=nation)
    assert refreshed_flag.content_hash == flag_hash_before


@pytest.mark.django_db
def test_apply_replaces_svg(
    published_variant, published_variant_dvar, published_variant_dsvg
):
    new_dsvg = published_variant_dsvg.replace(
        '<g id="background"', '<g id="background"><rect id="marker" width="1" height="1"/>', 1
    )
    hash_before = published_variant.svg.content_hash
    apply_safe_replacement(published_variant, published_variant_dvar, new_dsvg)
    refreshed = Variant.objects.get(id=published_variant.id)
    assert refreshed.svg.content_hash != hash_before


@pytest.mark.django_db
def test_apply_updates_variant_level_fields(
    published_variant, published_variant_dvar, published_variant_dsvg
):
    modified = copy.deepcopy(published_variant_dvar)
    modified["name"] = "Renamed Variant"
    modified["description"] = "Updated description"
    modified["rules"] = "New rules text"

    apply_safe_replacement(published_variant, modified, published_variant_dsvg)

    refreshed = Variant.objects.get(id=published_variant.id)
    assert refreshed.name == "Renamed Variant"
    assert refreshed.description == "Updated description"
    assert refreshed.rules == "New rules text"
