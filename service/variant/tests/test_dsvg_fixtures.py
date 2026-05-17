from pathlib import Path

import pytest

from variant.models import Variant
from variant.utils import normalize_dsvg, validate_dsvg

SVG_DIR = Path(__file__).resolve().parent.parent / "data" / "svg"

FIXTURE_VARIANTS = {
    "classical.d.svg": "classical",
    "hundred.d.svg": "hundred",
    "vietnam-war.d.svg": "vietnam-war",
    "canton.d.svg": "canton",
    "youngstown-redux.d.svg": "youngstown-redux",
}


@pytest.mark.django_db
@pytest.mark.parametrize("filename,variant_id", sorted(FIXTURE_VARIANTS.items()))
def test_committed_dsvg_passes_validation(filename, variant_id):
    svg = (SVG_DIR / filename).read_text()
    variant = Variant.objects.get(id=variant_id)

    assert validate_dsvg(svg, variant) == []


@pytest.mark.parametrize("filename", sorted(FIXTURE_VARIANTS))
def test_committed_dsvg_is_normalized(filename):
    svg = (SVG_DIR / filename).read_text()

    assert normalize_dsvg(svg) == svg
