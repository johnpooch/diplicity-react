import xml.etree.ElementTree as ElementTree

from variant.utils import DSVG_LAYER_ORDER, convert_godip_dsvg, normalize_dsvg, validate_dsvg


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _layers(svg):
    root = ElementTree.fromstring(svg)
    return {child.get("id"): child for child in root if _local_name(child.tag) == "g"}


def _path_ids(layer):
    return [
        element.get("id") for element in layer.iter() if _local_name(element.tag) == "path"
    ]


def _circles(layer):
    return [element for element in layer.iter() if _local_name(element.tag) == "circle"]


def _circle_ids(layer):
    return {circle.get("id") for circle in _circles(layer)}


def test_converts_to_canonical_layers(make_godip_svg):
    dsvg, warnings = convert_godip_dsvg(make_godip_svg())

    assert list(_layers(dsvg)) == DSVG_LAYER_ORDER
    assert warnings == []


def test_output_passes_validation_and_is_idempotent(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    assert validate_dsvg(dsvg) == []
    assert normalize_dsvg(dsvg) == dsvg


def test_inkscape_label_promoted_to_id(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    assert set(_path_ids(_layers(dsvg)["provinces"])) == {"fra", "ber"}


def test_polygon_converted_to_path(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    ber = [el for el in _layers(dsvg)["provinces"].iter() if el.get("id") == "ber"][0]
    assert _local_name(ber.tag) == "path"
    assert ber.get("points") is None
    assert ber.get("d") == "M 2,2 3,3 4,4 Z"


def test_named_coast_paths_moved_to_named_coasts_layer(make_godip_svg):
    layers = _layers(convert_godip_dsvg(make_godip_svg())[0])

    assert _path_ids(layers["named-coasts"]) == ["fra/nc"]
    assert "fra/nc" not in _path_ids(layers["provinces"])


def test_runtime_layers_dropped(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    assert set(_layers(dsvg)) == set(DSVG_LAYER_ORDER)


def test_godip_names_become_province_names(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    province_names = _layers(dsvg)["province-names"]
    texts = [el.get("id") for el in province_names.iter() if _local_name(el.tag) == "text"]
    assert texts == ["France"]


def test_noise_folded_into_foreground(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    foreground = _layers(dsvg)["foreground"]
    assert any(el.get("id") == "Noise" for el in foreground.iter())


def test_provinces_and_named_coasts_are_hidden(make_godip_svg):
    layers = _layers(convert_godip_dsvg(make_godip_svg())[0])

    for layer_id in ("provinces", "named-coasts"):
        assert "display:none" in (layers[layer_id].get("style") or "")


def test_unit_positions_and_supply_centers_are_hidden(make_godip_svg):
    layers = _layers(convert_godip_dsvg(make_godip_svg())[0])

    for layer_id in ("unit-positions", "supply-centers"):
        assert "display:none" in (layers[layer_id].get("style") or "")


def test_godip_centers_become_unit_positions(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    assert _circle_ids(_layers(dsvg)["unit-positions"]) == {"fra", "fra/nc", "ber"}


def test_godip_supply_centers_layer_mapped(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    assert _circle_ids(_layers(dsvg)["supply-centers"]) == {"ber"}


def test_center_path_converted_to_circle_at_moveto_anchor(make_godip_svg):
    dsvg, _ = convert_godip_dsvg(make_godip_svg())

    fra = [c for c in _circles(_layers(dsvg)["unit-positions"]) if c.get("id") == "fra"][0]
    assert (fra.get("cx"), fra.get("cy")) == ("20", "21")


def test_missing_layers_are_synthesized(make_godip_svg):
    svg = make_godip_svg(layers={"background": "", "provinces": ""})

    dsvg, _ = convert_godip_dsvg(svg)

    assert list(_layers(dsvg)) == DSVG_LAYER_ORDER
    assert validate_dsvg(dsvg) == []


def test_missing_center_layers_are_warned(make_godip_svg):
    svg = make_godip_svg(layers={"background": "", "provinces": ""})

    _, warnings = convert_godip_dsvg(svg)

    assert "Input has no 'province-centers' layer." in warnings
    assert "Input has no 'supply-centers' layer." in warnings


def test_province_centers_without_named_coasts_warns(make_godip_svg):
    svg = make_godip_svg(
        layers={
            "background": "",
            "provinces": "",
            "province-centers": '<path id="fraCenter" d="m 1,2 c 0,0"/>',
            "supply-centers": '<path id="berCenter" d="m 3,4 c 0,0"/>',
            "foreground": "",
            "names": "",
        }
    )

    _, warnings = convert_godip_dsvg(svg)

    assert "'unit-positions' layer has no named-coast entries." in warnings


def test_province_subgroup_is_flattened():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" viewBox="0 0 10 10">'
        '<g inkscape:label="provinces" id="provinces">'
        '<g inkscape:label="fra" id="g1"><path d="M0 0 L1 1"/><path d="M2 2 L3 3"/></g>'
        "</g></svg>"
    )

    dsvg, _ = convert_godip_dsvg(svg)

    paths = [el for el in _layers(dsvg)["provinces"].iter() if _local_name(el.tag) == "path"]
    assert len(paths) == 1
    assert paths[0].get("id") == "fra"
    assert paths[0].get("d") == "M0 0 L1 1 M2 2 L3 3"


def test_supply_centers_foreground_copy_is_dropped(make_godip_svg):
    svg = make_godip_svg(
        layers={
            "background": "",
            "provinces": "",
            "province-centers": '<path id="fra/ncCenter" d="m 1,2 c 0,0"/>',
            "supply-centers": '<path id="berCenter" d="m 3,4 c 0,0"/>',
            "foreground": "",
            "names": "",
        }
    )
    svg = svg.replace(
        "</svg>",
        '<g inkscape:label="supply-centers foreground copy" id="g1374">'
        '<circle id="sc-copy" r="1"/></g></svg>',
    )

    dsvg, warnings = convert_godip_dsvg(svg)

    assert "sc-copy" not in dsvg
    assert warnings == []
