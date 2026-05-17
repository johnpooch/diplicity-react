import pytest

from common.constants import ProvinceType
from province.models import Province
from variant.models import Variant
from variant.utils import DSVG_HIDDEN_LAYERS, DSVG_LAYER_ORDER


@pytest.fixture
def make_dsvg():
    def _make(
        layer_ids=None,
        hidden_layers=DSVG_HIDDEN_LAYERS,
        province_ids=None,
        named_coast_ids=None,
        unit_position_ids=None,
        supply_center_ids=None,
    ):
        if layer_ids is None:
            layer_ids = DSVG_LAYER_ORDER

        def _paths(path_ids):
            if path_ids is None:
                return ""
            return "".join(
                f'<path id="{path_id}"/>' if path_id is not None else "<path/>"
                for path_id in path_ids
            )

        def _circles(circle_ids):
            if circle_ids is None:
                return ""
            return "".join(
                f'<circle id="{circle_id}" cx="0" cy="0"/>' if circle_id is not None else "<circle/>"
                for circle_id in circle_ids
            )

        def _layer(layer_id):
            style = ' style="display:none"' if layer_id in hidden_layers else ""
            content = ""
            if layer_id == "provinces":
                content = _paths(province_ids)
            elif layer_id == "named-coasts":
                content = _paths(named_coast_ids)
            elif layer_id == "unit-positions":
                content = _circles(unit_position_ids)
            elif layer_id == "supply-centers":
                content = _circles(supply_center_ids)
            return f'  <g id="{layer_id}"{style}>{content}</g>'

        layers = "\n".join(_layer(layer_id) for layer_id in layer_ids)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\n'
            f"{layers}\n"
            "</svg>"
        )

    return _make


@pytest.fixture
def make_editor_dsvg():
    def _make(layer_ids=None):
        if layer_ids is None:
            layer_ids = DSVG_LAYER_ORDER

        def _layer(layer_id):
            style = ' style="display:none"' if layer_id in DSVG_HIDDEN_LAYERS else ""
            return (
                f'  <g id="{layer_id}" inkscape:groupmode="layer" '
                f'inkscape:label="{layer_id}" sodipodi:insensitive="true" '
                f'i:knockout="Off" data-name="{layer_id}"{style}></g>'
            )

        layers = "\n".join(_layer(layer_id) for layer_id in layer_ids)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd" '
            'xmlns:i="http://ns.adobe.com/AdobeIllustrator/10.0/" '
            'viewBox="0 0 100 100">\n'
            "  <!-- Generator: Adobe Illustrator -->\n"
            '  <metadata id="metadata1">editor metadata</metadata>\n'
            '  <sodipodi:namedview id="namedview1"/>\n'
            f"{layers}\n"
            "</svg>"
        )

    return _make


@pytest.fixture
def make_godip_svg():
    def _make(layers=None):
        if layers is None:
            layers = {
                "background": '<rect id="sea" width="100" height="100"/>',
                "provinces": (
                    '<path inkscape:label="fra" id="path1" d="M0 0 L1 1 Z"/>'
                    '<polygon inkscape:label="ber" id="poly1" points="2,2 3,3 4,4"/>'
                    '<path inkscape:label="fra/nc" id="path2" d="M5 5 L6 6 Z"/>'
                ),
                "supply-centers": '<path id="berCenter" d="m 10,11 c 1,1 2,2 3,3"/>',
                "province-centers": (
                    '<path id="fraCenter" d="m 20,21 c 1,1 2,2 3,3"/>'
                    '<path id="fra/ncCenter" d="m 30,31 c 1,1 2,2 3,3"/>'
                ),
                "highlights": "",
                "foreground": '<path id="coast" d="M0 0 L9 9"/>',
                "names": '<text id="France">France</text>',
                "units": "",
                "orders": "",
            }
        layer_xml = "".join(
            f'<g inkscape:groupmode="layer" inkscape:label="{layer_id}" id="{layer_id}">'
            f"{content}</g>"
            for layer_id, content in layers.items()
        )
        noise = (
            '<g inkscape:groupmode="layer" inkscape:label="noise" id="layer99">'
            '<rect id="Noise" width="100" height="100"/></g>'
        )
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" '
            'viewBox="0 0 100 100">'
            '<sodipodi:namedview id="namedview1"/>'
            '<defs id="defs1"><linearGradient id="grad1"/></defs>'
            f"{layer_xml}{noise}"
            "</svg>"
        )

    return _make


@pytest.fixture
def dsvg_variant(db):
    variant = Variant.objects.create(
        id="dsvg-test-variant",
        name="dSVG Test Variant",
        description="",
        author="Test",
    )
    france = Province.objects.create(
        province_id="fra",
        name="France",
        type=ProvinceType.COASTAL,
        supply_center=True,
        variant=variant,
    )
    Province.objects.create(province_id="ger", name="Germany", type=ProvinceType.LAND, variant=variant)
    Province.objects.create(
        province_id="fra/nc",
        name="France (north coast)",
        type=ProvinceType.NAMED_COAST,
        variant=variant,
        parent=france,
    )
    return variant
