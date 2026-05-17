import hashlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from variant.admin import VariantSvgAdminForm
from variant.models import Variant, VariantSvg
from variant.utils import normalize_dsvg


def _upload(svg):
    return SimpleUploadedFile("map.d.svg", svg.encode(), content_type="image/svg+xml")


@pytest.mark.django_db
def test_content_hash_is_computed_on_save(dsvg_variant):
    variant_svg = VariantSvg.objects.create(variant=dsvg_variant, svg="<svg/>")

    assert variant_svg.content_hash == hashlib.sha256(b"<svg/>").hexdigest()


@pytest.mark.django_db
def test_content_hash_is_recomputed_when_svg_changes(dsvg_variant):
    variant_svg = VariantSvg.objects.create(variant=dsvg_variant, svg="<svg/>")
    original = variant_svg.content_hash

    variant_svg.svg = "<svg><g/></svg>"
    variant_svg.save()

    assert variant_svg.content_hash != original


@pytest.mark.django_db
def test_variant_has_at_most_one_svg(dsvg_variant):
    VariantSvg.objects.create(variant=dsvg_variant, svg="<svg/>")

    with pytest.raises(IntegrityError):
        VariantSvg.objects.create(variant=dsvg_variant, svg="<svg/>")


@pytest.mark.django_db
def test_admin_form_accepts_valid_upload(dsvg_variant, make_dsvg):
    svg = make_dsvg(
        province_ids=["fra", "ger"],
        named_coast_ids=["fra/nc"],
        unit_position_ids=["fra", "ger", "fra/nc"],
    )

    form = VariantSvgAdminForm(data={"variant": dsvg_variant.pk}, files={"svg_file": _upload(svg)})

    assert form.is_valid(), form.errors
    instance = form.save()
    assert instance.svg == normalize_dsvg(svg)
    assert instance.content_hash == hashlib.sha256(normalize_dsvg(svg).encode()).hexdigest()


@pytest.mark.django_db
def test_admin_form_rejects_svg_not_matching_variant(dsvg_variant, make_dsvg):
    svg = make_dsvg(province_ids=["fra", "xyz"], named_coast_ids=["fra/nc"])

    form = VariantSvgAdminForm(data={"variant": dsvg_variant.pk}, files={"svg_file": _upload(svg)})

    assert not form.is_valid()


@pytest.mark.django_db
def test_admin_form_rejects_malformed_xml(dsvg_variant):
    form = VariantSvgAdminForm(
        data={"variant": dsvg_variant.pk}, files={"svg_file": _upload("<svg><g></svg>")}
    )

    assert not form.is_valid()


@pytest.mark.django_db
def test_admin_form_requires_a_file_on_add(dsvg_variant):
    form = VariantSvgAdminForm(data={"variant": dsvg_variant.pk}, files={})

    assert not form.is_valid()


@pytest.mark.django_db
def test_admin_form_normalizes_uploaded_svg(make_editor_dsvg):
    variant = Variant.objects.create(id="empty", name="Empty", description="", author="")

    form = VariantSvgAdminForm(
        data={"variant": variant.pk}, files={"svg_file": _upload(make_editor_dsvg())}
    )

    assert form.is_valid(), form.errors
    instance = form.save()
    assert "inkscape" not in instance.svg
    assert "<!--" not in instance.svg
