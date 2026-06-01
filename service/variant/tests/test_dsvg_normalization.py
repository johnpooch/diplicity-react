from variant.utils import normalize_dsvg, validate_dsvg


def test_normalize_strips_all_foreign_namespaces(make_editor_dsvg):
    result = normalize_dsvg(make_editor_dsvg())

    for token in ("inkscape", "sodipodi", "AdobeIllustrator", "namedview"):
        assert token not in result


def test_normalize_strips_no_namespace_noise(make_editor_dsvg):
    result = normalize_dsvg(make_editor_dsvg())

    assert "data-name" not in result
    assert "<!--" not in result
    assert "metadata" not in result


def test_normalize_is_idempotent(make_editor_dsvg):
    once = normalize_dsvg(make_editor_dsvg())
    twice = normalize_dsvg(once)

    assert twice == once


def test_normalize_preserves_svg_content(make_editor_dsvg):
    result = normalize_dsvg(make_editor_dsvg())

    assert "viewBox" in result
    assert validate_dsvg(result) == []


def test_normalize_strips_svg_namespace_prefix_on_elements():
    svg = (
        '<svg xmlns:svg="http://www.w3.org/2000/svg" '
        'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<svg:g id="background"><svg:rect width="10" height="10"/></svg:g>'
        '<svg:g id="provinces" style="display:none">'
        '<svg:path id="alpha" d="M0 0 L1 1"/>'
        "</svg:g>"
        "</svg>"
    )

    result = normalize_dsvg(svg)

    assert "<svg:" not in result
    assert "</svg:" not in result
    assert 'xmlns:svg="' not in result
    assert '<g id="background">' in result
    assert '<path id="alpha"' in result


def test_normalize_strips_svg_namespace_prefix_is_idempotent():
    svg = (
        '<svg xmlns:svg="http://www.w3.org/2000/svg" '
        'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<svg:g id="background"></svg:g>'
        "</svg>"
    )

    once = normalize_dsvg(svg)
    twice = normalize_dsvg(once)

    assert once == twice


def test_normalize_sets_radius_on_unit_position_circles():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="unit-positions" style="display:none">'
        '<circle id="alpha" cx="10" cy="10"/>'
        '<circle id="beta" cx="20" cy="20" r="0"/>'
        '<circle id="gamma" cx="30" cy="30" r="5"/>'
        "</g>"
        "</svg>"
    )

    result = normalize_dsvg(svg)

    assert result.count('r="10"') == 3
    assert 'r="0"' not in result
    assert 'r="5"' not in result


def test_normalize_sets_radius_on_supply_center_circles_when_present():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="supply-centers" style="display:none">'
        '<circle id="alpha" cx="10" cy="10"/>'
        "</g>"
        "</svg>"
    )

    result = normalize_dsvg(svg)

    assert 'r="10"' in result


def test_normalize_leaves_circles_in_other_layers_alone():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="foreground">'
        '<circle cx="5" cy="5" r="3"/>'
        "</g>"
        "</svg>"
    )

    result = normalize_dsvg(svg)

    assert 'r="3"' in result
