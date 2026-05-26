import pytest

from common.constants import VariantStatus
from nation.models import Nation
from variant.models import Variant


@pytest.fixture
def draft_variant_for_primary(db, primary_user):
    variant = Variant.objects.create(
        id="primary-draft",
        name="Primary Draft",
        description="",
        status=VariantStatus.DRAFT,
        owner=primary_user,
    )
    Nation.objects.create(variant=variant, nation_id="reds", name="Reds", color="#ff0000")
    Nation.objects.create(variant=variant, nation_id="blues", name="Blues", color="#0000ff")
    return variant


@pytest.fixture
def draft_variant_for_secondary(db, secondary_user):
    variant = Variant.objects.create(
        id="secondary-draft",
        name="Secondary Draft",
        description="",
        status=VariantStatus.DRAFT,
        owner=secondary_user,
    )
    Nation.objects.create(variant=variant, nation_id="greens", name="Greens", color="#00ff00")
    return variant


@pytest.fixture
def minimal_flag_svg():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<rect width="10" height="10" fill="#ff0000"/>'
        "</svg>"
    )
