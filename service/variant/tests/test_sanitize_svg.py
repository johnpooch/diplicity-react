from variant.utils import sanitize_svg


def test_strips_script_elements():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<script>alert(1)</script>'
        '<rect id="r1"/>'
        "</svg>"
    )
    out = sanitize_svg(svg)
    assert "<script" not in out
    assert "alert" not in out
    assert 'id="r1"' in out


def test_strips_on_event_handler_attributes():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<rect id="r1" onclick="alert(1)" onmouseover="alert(2)"/>'
        "</svg>"
    )
    out = sanitize_svg(svg)
    assert "onclick" not in out
    assert "onmouseover" not in out
    assert 'id="r1"' in out


def test_strips_foreign_object():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<foreignObject><div>injected</div></foreignObject>'
        "</svg>"
    )
    out = sanitize_svg(svg)
    assert "foreignObject" not in out
    assert "injected" not in out


def test_strips_javascript_url_in_href():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<a xlink:href="javascript:alert(1)"><rect id="r1"/></a>'
        "</svg>"
    )
    out = sanitize_svg(svg)
    assert "javascript:" not in out
    assert 'id="r1"' in out


def test_preserves_normal_svg_content():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect id="r1" width="10" height="10" fill="#ff0000"/>'
        '<circle cx="50" cy="50" r="20"/>'
        '<path id="p1" d="M0 0 L10 10 Z" style="fill:none;stroke:#000"/>'
        "</svg>"
    )
    out = sanitize_svg(svg)
    assert 'id="r1"' in out
    assert 'id="p1"' in out
    assert "fill=\"#ff0000\"" in out
    assert "M0 0 L10 10 Z" in out


def test_idempotent():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<script>x</script><rect id="r1" onclick="x"/>'
        "</svg>"
    )
    once = sanitize_svg(svg)
    twice = sanitize_svg(once)
    assert once == twice
