import pytest

from common.constants import ProvinceType
from province.models import Province
from variant.models import Variant
from variant.utils import DSVG_HIDDEN_LAYERS, DSVG_LAYER_ORDER


@pytest.fixture
def make_dsvg():
    def _make(layer_ids=None, hidden_layers=DSVG_HIDDEN_LAYERS, province_ids=None, named_coast_ids=None):
        if layer_ids is None:
            layer_ids = DSVG_LAYER_ORDER

        def _paths(path_ids):
            if path_ids is None:
                return ""
            return "".join(
                f'<path id="{path_id}"/>' if path_id is not None else "<path/>"
                for path_id in path_ids
            )

        def _layer(layer_id):
            style = ' style="display:none"' if layer_id in hidden_layers else ""
            content = ""
            if layer_id == "provinces":
                content = _paths(province_ids)
            elif layer_id == "named-coasts":
                content = _paths(named_coast_ids)
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
def dsvg_variant(db):
    variant = Variant.objects.create(
        id="dsvg-test-variant",
        name="dSVG Test Variant",
        description="",
        author="Test",
    )
    france = Province.objects.create(
        province_id="fra", name="France", type=ProvinceType.COASTAL, variant=variant
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
