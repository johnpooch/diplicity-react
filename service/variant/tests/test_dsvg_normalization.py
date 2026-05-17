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
