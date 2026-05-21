from adjudicator.domain import (
    Adjacency,
    NamedCoast,
    Nation,
    OrderOption,
    PhaseProgression,
    PhaseTransition,
    Province,
    ProvinceType,
    SupplyCenter,
    Unit,
    Variant,
)
from adjudication.options_adapter import python_options_to_godip_dict
from phase.utils import transform_options


def _coastal(province_id, adjacencies=(), home_nation=None, supply_center=False):
    return Province(
        id=province_id,
        name=province_id,
        type=ProvinceType.COASTAL,
        supply_center=supply_center,
        home_nation=home_nation,
        adjacencies=tuple(adjacencies),
    )


def _make_variant(provinces=None, named_coasts=None, nations=None):
    provinces = {p.id: p for p in (provinces or [])}
    named_coasts = {nc.id: nc for nc in (named_coasts or [])}
    nations = tuple(nations or [Nation(id="ENG", name="England", color="#fff")])
    return Variant(
        id="test",
        name="test",
        description="",
        author="",
        victory_conditions=(),
        rules=None,
        adjudication_modifiers=(),
        phase_progression=PhaseProgression(seasons=("Spring",), transitions=()),
        nations=nations,
        provinces=provinces,
        named_coasts=named_coasts,
        dominance_rules=(),
    )


def test_hold_option_produces_terminal_src_province_subtree():
    variant = _make_variant(provinces=[_coastal("lon")])
    options = [
        OrderOption(
            source="lon",
            order_type="Hold",
            target=None,
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="ENG", type=Unit.ARMY, location="lon")]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    assert result == {
        "England": {
            "lon": {
                "Type": "Province",
                "Next": {
                    "Hold": {
                        "Type": "OrderType",
                        "Next": {
                            "lon": {"Type": "SrcProvince", "Next": {}},
                        },
                    },
                },
            },
        },
    }


def test_move_option_includes_target_under_src_province():
    variant = _make_variant(provinces=[_coastal("lon"), _coastal("wal")])
    options = [
        OrderOption(
            source="lon",
            order_type="Move",
            target="wal",
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="ENG", type=Unit.ARMY, location="lon")]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    src_next = result["England"]["lon"]["Next"]["Move"]["Next"]["lon"]["Next"]
    assert src_next == {"wal": {"Type": "Province", "Next": {}}}


def test_support_hold_uses_aux_equal_to_target():
    variant = _make_variant(provinces=[_coastal("lon"), _coastal("wal")])
    options = [
        OrderOption(
            source="lon",
            order_type="Support",
            target="wal",
            aux="wal",
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [
        Unit(nation="ENG", type=Unit.ARMY, location="lon"),
        Unit(nation="ENG", type=Unit.ARMY, location="wal"),
    ]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    src_next = result["England"]["lon"]["Next"]["Support"]["Next"]["lon"]["Next"]
    assert src_next == {
        "wal": {"Type": "Province", "Next": {"wal": {"Type": "Province", "Next": {}}}},
    }


def test_support_move_nests_target_under_aux():
    variant = _make_variant(provinces=[_coastal("lon"), _coastal("wal"), _coastal("yor")])
    options = [
        OrderOption(
            source="lon",
            order_type="Support",
            target="yor",
            aux="wal",
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [
        Unit(nation="ENG", type=Unit.ARMY, location="lon"),
        Unit(nation="ENG", type=Unit.ARMY, location="wal"),
    ]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    src_next = result["England"]["lon"]["Next"]["Support"]["Next"]["lon"]["Next"]
    assert src_next == {
        "wal": {
            "Type": "Province",
            "Next": {"yor": {"Type": "Province", "Next": {}}},
        },
    }


def test_convoy_option_nests_army_target_under_army_source():
    variant = _make_variant(provinces=[_coastal("eng"), _coastal("lon"), _coastal("bre")])
    options = [
        OrderOption(
            source="eng",
            order_type="Convoy",
            target="bre",
            aux="lon",
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="ENG", type=Unit.FLEET, location="eng")]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    src_next = result["England"]["eng"]["Next"]["Convoy"]["Next"]["eng"]["Next"]
    assert src_next == {
        "lon": {
            "Type": "Province",
            "Next": {"bre": {"Type": "Province", "Next": {}}},
        },
    }


def test_build_army_keyed_by_supply_center_owner():
    variant = _make_variant(
        provinces=[_coastal("lon", supply_center=True, home_nation="ENG")],
    )
    options = [
        OrderOption(
            source="lon",
            order_type="Build",
            target="lon",
            aux=None,
            unit_type="Army",
            named_coast=None,
        ),
    ]
    supply_centers = [SupplyCenter(nation="ENG", province="lon")]

    result = python_options_to_godip_dict(options, [], supply_centers, variant, "Adjustment")

    assert result["England"]["lon"]["Next"]["Build"]["Next"] == {
        "Army": {
            "Type": "UnitType",
            "Next": {"lon": {"Type": "SrcProvince", "Next": {}}},
        },
    }


def test_build_fleet_at_named_coast_uses_coast_as_source_key():
    parent = _coastal("stp", supply_center=True, home_nation="RUS")
    named_coast = NamedCoast(
        id="stp/nc", name="stp/nc", parent_province="stp", adjacencies=()
    )
    variant = _make_variant(
        provinces=[parent],
        named_coasts=[named_coast],
        nations=[Nation(id="RUS", name="Russia", color="#fff")],
    )
    options = [
        OrderOption(
            source="stp/nc",
            order_type="Build",
            target="stp/nc",
            aux=None,
            unit_type="Fleet",
            named_coast=None,
        ),
    ]
    supply_centers = [SupplyCenter(nation="RUS", province="stp")]

    result = python_options_to_godip_dict(options, [], supply_centers, variant, "Adjustment")

    assert "stp/nc" in result["Russia"]
    assert result["Russia"]["stp/nc"]["Next"]["Build"]["Next"] == {
        "Fleet": {
            "Type": "UnitType",
            "Next": {"stp/nc": {"Type": "SrcProvince", "Next": {}}},
        },
    }


def test_move_via_convoy_emitted_as_separate_order_type():
    variant = _make_variant(provinces=[_coastal("lon"), _coastal("nor")])
    options = [
        OrderOption(
            source="lon",
            order_type="Move",
            target="nor",
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
        OrderOption(
            source="lon",
            order_type="MoveViaConvoy",
            target="nor",
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="ENG", type=Unit.ARMY, location="lon")]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    lon_next = result["England"]["lon"]["Next"]
    assert "Move" in lon_next
    assert "MoveViaConvoy" in lon_next
    assert lon_next["Move"]["Next"]["lon"]["Next"] == {
        "nor": {"Type": "Province", "Next": {}}
    }
    assert lon_next["MoveViaConvoy"]["Next"]["lon"]["Next"] == {
        "nor": {"Type": "Province", "Next": {}}
    }


def test_retreat_option_emits_move_order_type_under_dislodged_unit():
    variant = _make_variant(provinces=[_coastal("lon"), _coastal("wal")])
    options = [
        OrderOption(
            source="lon",
            order_type="Retreat",
            target="wal",
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="ENG", type=Unit.ARMY, location="lon", dislodged=True)]

    result = python_options_to_godip_dict(options, units, [], variant, "Retreat")

    assert "Move" in result["England"]["lon"]["Next"]
    assert "Retreat" not in result["England"]["lon"]["Next"]
    src_next = result["England"]["lon"]["Next"]["Move"]["Next"]["lon"]["Next"]
    assert src_next == {"wal": {"Type": "Province", "Next": {}}}


def test_unit_on_named_coast_keys_options_under_parent_province():
    parent = _coastal("stp")
    named = NamedCoast(id="stp/sc", name="stp/sc", parent_province="stp", adjacencies=())
    variant = _make_variant(
        provinces=[parent, _coastal("fin")],
        named_coasts=[named],
        nations=[Nation(id="RUS", name="Russia", color="#fff")],
    )
    options = [
        OrderOption(
            source="stp/sc",
            order_type="Hold",
            target=None,
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="RUS", type=Unit.FLEET, location="stp/sc")]

    result = python_options_to_godip_dict(options, units, [], variant, "Movement")

    assert "stp" in result["Russia"]
    assert "stp/sc" not in result["Russia"]


def test_disband_option_under_adjustment_phase():
    variant = _make_variant(provinces=[_coastal("lon")])
    options = [
        OrderOption(
            source="lon",
            order_type="Disband",
            target=None,
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    units = [Unit(nation="ENG", type=Unit.ARMY, location="lon")]

    result = python_options_to_godip_dict(options, units, [], variant, "Adjustment")

    assert result["England"]["lon"]["Next"]["Disband"]["Next"] == {
        "lon": {"Type": "SrcProvince", "Next": {}},
    }


def test_nation_without_orders_present_as_empty_dict():
    variant = _make_variant(
        provinces=[_coastal("lon")],
        nations=[
            Nation(id="ENG", name="England", color="#fff"),
            Nation(id="FRA", name="France", color="#fff"),
        ],
    )
    result = python_options_to_godip_dict([], [], [], variant, "Movement")
    assert result == {"England": {}, "France": {}}


def test_adapter_output_is_consumable_by_transform_options():
    """End-to-end shape check: the godip-format dict the adapter produces
    must pass cleanly through phase.utils.transform_options — that's the
    function the frontend's options tree ultimately came from godip via."""
    parent = _coastal("stp", supply_center=True, home_nation="RUS")
    nc = NamedCoast(id="stp/nc", name="stp/nc", parent_province="stp", adjacencies=())
    sc = NamedCoast(id="stp/sc", name="stp/sc", parent_province="stp", adjacencies=())
    variant = _make_variant(
        provinces=[parent, _coastal("lon"), _coastal("wal"), _coastal("yor")],
        named_coasts=[nc, sc],
        nations=[
            Nation(id="ENG", name="England", color="#fff"),
            Nation(id="RUS", name="Russia", color="#fff"),
        ],
    )
    options = [
        OrderOption(source="lon", order_type="Hold", target=None, aux=None, unit_type=None, named_coast=None),
        OrderOption(source="lon", order_type="Move", target="wal", aux=None, unit_type=None, named_coast=None),
        OrderOption(source="lon", order_type="Support", target="wal", aux="wal", unit_type=None, named_coast=None),
        OrderOption(source="lon", order_type="Support", target="yor", aux="wal", unit_type=None, named_coast=None),
        OrderOption(source="stp/nc", order_type="Build", target="stp/nc", aux=None, unit_type="Fleet", named_coast=None),
        OrderOption(source="stp/sc", order_type="Build", target="stp/sc", aux=None, unit_type="Fleet", named_coast=None),
        OrderOption(source="stp", order_type="Build", target="stp", aux=None, unit_type="Army", named_coast=None),
    ]
    units = [
        Unit(nation="ENG", type=Unit.ARMY, location="lon"),
        Unit(nation="ENG", type=Unit.ARMY, location="wal"),
    ]
    supply_centers = [SupplyCenter(nation="RUS", province="stp")]

    raw = python_options_to_godip_dict(options, units, supply_centers, variant, "Adjustment")
    transformed = transform_options(raw)

    assert transformed["England"]["lon"] == {
        "Hold": {},
        "Move": {"wal": {}},
        "Support": {"wal": {"wal": {}, "yor": {}}},
    }
    # Build options at named coasts are merged under the parent province.
    assert "stp" in transformed["Russia"]
    assert "stp/nc" not in transformed["Russia"]
    assert "stp/sc" not in transformed["Russia"]
    build = transformed["Russia"]["stp"]["Build"]
    assert build["Army"] == {}
    assert set(build["Fleet"].keys()) == {"stp/nc", "stp/sc"}


def test_option_for_location_with_no_owning_nation_is_dropped():
    variant = _make_variant(provinces=[_coastal("lon")])
    options = [
        OrderOption(
            source="lon",
            order_type="Hold",
            target=None,
            aux=None,
            unit_type=None,
            named_coast=None,
        ),
    ]
    result = python_options_to_godip_dict(options, [], [], variant, "Movement")
    assert result == {"England": {}}
