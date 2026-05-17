import pytest

from variant.utils import DSVG_LAYER_ORDER, validate_dsvg


def test_valid_dsvg_has_no_errors(make_dsvg):
    assert validate_dsvg(make_dsvg()) == []


def test_missing_layer_is_reported(make_dsvg):
    layer_ids = [layer for layer in DSVG_LAYER_ORDER if layer != "foreground"]

    errors = validate_dsvg(make_dsvg(layer_ids=layer_ids))

    assert [error.code for error in errors] == ["MISSING_LAYER"]


def test_layers_out_of_order_is_reported(make_dsvg):
    layer_ids = ["provinces", "background"] + DSVG_LAYER_ORDER[2:]

    errors = validate_dsvg(make_dsvg(layer_ids=layer_ids))

    assert [error.code for error in errors] == ["LAYER_OUT_OF_ORDER"]


def test_unexpected_layer_is_reported(make_dsvg):
    layer_ids = DSVG_LAYER_ORDER + ["decoration"]

    errors = validate_dsvg(make_dsvg(layer_ids=layer_ids))

    assert [error.code for error in errors] == ["UNEXPECTED_LAYER"]


def test_unhidden_provinces_layer_is_reported(make_dsvg):
    errors = validate_dsvg(make_dsvg(hidden_layers=("named-coasts", "unit-positions")))

    assert [error.code for error in errors] == ["LAYER_NOT_HIDDEN"]


def test_unhidden_named_coasts_layer_is_reported(make_dsvg):
    errors = validate_dsvg(make_dsvg(hidden_layers=("provinces", "unit-positions")))

    assert [error.code for error in errors] == ["LAYER_NOT_HIDDEN"]


def test_unhidden_unit_positions_layer_is_reported(make_dsvg):
    errors = validate_dsvg(make_dsvg(hidden_layers=("provinces", "named-coasts")))

    assert [error.code for error in errors] == ["LAYER_NOT_HIDDEN"]


def test_province_path_without_id_is_reported(make_dsvg):
    errors = validate_dsvg(make_dsvg(province_ids=["fra", None, "ger"]))

    assert [error.code for error in errors] == ["PROVINCE_MISSING_ID"]


def test_named_coast_path_with_invalid_id_is_reported(make_dsvg):
    errors = validate_dsvg(make_dsvg(named_coast_ids=["stp/nc", "spa"]))

    assert [error.code for error in errors] == ["NAMED_COAST_INVALID_ID"]


def test_valid_province_and_named_coast_paths_pass(make_dsvg):
    errors = validate_dsvg(make_dsvg(province_ids=["fra", "ger"], named_coast_ids=["stp/nc"]))

    assert errors == []


@pytest.mark.django_db
def test_unknown_province_is_reported(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra", "ger", "xyz"],
            named_coast_ids=["fra/nc"],
            unit_position_ids=["fra", "ger", "fra/nc"],
        ),
        variant=dsvg_variant,
    )

    assert [error.code for error in errors] == ["UNKNOWN_PROVINCE"]


@pytest.mark.django_db
def test_missing_province_is_reported(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra"],
            named_coast_ids=["fra/nc"],
            unit_position_ids=["fra", "ger", "fra/nc"],
        ),
        variant=dsvg_variant,
    )

    assert [error.code for error in errors] == ["MISSING_PROVINCE"]


@pytest.mark.django_db
def test_dsvg_matching_variant_passes(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra", "ger"],
            named_coast_ids=["fra/nc"],
            unit_position_ids=["fra", "ger", "fra/nc"],
        ),
        variant=dsvg_variant,
    )

    assert errors == []


@pytest.mark.django_db
def test_unknown_named_coast_is_reported(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra", "ger"],
            named_coast_ids=["fra/nc", "xyz/nc"],
            unit_position_ids=["fra", "ger", "fra/nc"],
        ),
        variant=dsvg_variant,
    )

    assert [error.code for error in errors] == ["UNKNOWN_NAMED_COAST"]


@pytest.mark.django_db
def test_missing_named_coast_is_reported(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra", "ger"],
            named_coast_ids=[],
            unit_position_ids=["fra", "ger", "fra/nc"],
        ),
        variant=dsvg_variant,
    )

    assert [error.code for error in errors] == ["MISSING_NAMED_COAST"]


@pytest.mark.django_db
def test_unknown_unit_position_is_reported(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra", "ger"],
            named_coast_ids=["fra/nc"],
            unit_position_ids=["fra", "ger", "fra/nc", "zzz"],
        ),
        variant=dsvg_variant,
    )

    assert [error.code for error in errors] == ["UNKNOWN_UNIT_POSITION"]


@pytest.mark.django_db
def test_missing_unit_position_is_reported(make_dsvg, dsvg_variant):
    errors = validate_dsvg(
        make_dsvg(
            province_ids=["fra", "ger"],
            named_coast_ids=["fra/nc"],
            unit_position_ids=["fra", "ger"],
        ),
        variant=dsvg_variant,
    )

    assert [error.code for error in errors] == ["MISSING_UNIT_POSITION"]


def test_malformed_xml_is_reported():
    errors = validate_dsvg("<svg><g></svg>")

    assert [error.code for error in errors] == ["MALFORMED_XML"]
