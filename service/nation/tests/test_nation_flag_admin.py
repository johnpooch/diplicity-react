import hashlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from nation.admin import NationFlagAdminForm
from nation.models import NationFlag
from nation.views import FLAG_MAX_BYTES


def _upload(svg, name="flag.svg"):
    return SimpleUploadedFile(name, svg.encode(), content_type="image/svg+xml")


@pytest.mark.django_db
def test_admin_form_accepts_valid_upload(draft_variant_for_primary, minimal_flag_svg):
    nation = draft_variant_for_primary.nations.first()

    form = NationFlagAdminForm(
        data={"nation": nation.pk}, files={"svg_file": _upload(minimal_flag_svg)}
    )

    assert form.is_valid(), form.errors
    instance = form.save()
    assert instance.nation == nation
    assert instance.content_hash == hashlib.sha256(instance.svg.encode()).hexdigest()


@pytest.mark.django_db
def test_admin_form_replaces_existing_flag(draft_variant_for_primary, minimal_flag_svg):
    nation = draft_variant_for_primary.nations.first()
    existing = NationFlag.objects.create(nation=nation, svg="<svg/>")
    original_hash = existing.content_hash

    form = NationFlagAdminForm(
        data={"nation": nation.pk},
        files={"svg_file": _upload(minimal_flag_svg)},
        instance=existing,
    )

    assert form.is_valid(), form.errors
    instance = form.save()
    assert instance.content_hash != original_hash


@pytest.mark.django_db
def test_admin_form_rejects_malformed_xml(draft_variant_for_primary):
    nation = draft_variant_for_primary.nations.first()

    form = NationFlagAdminForm(
        data={"nation": nation.pk}, files={"svg_file": _upload("<svg><g></svg>")}
    )

    assert not form.is_valid()


@pytest.mark.django_db
def test_admin_form_requires_a_file_on_add(draft_variant_for_primary):
    nation = draft_variant_for_primary.nations.first()

    form = NationFlagAdminForm(data={"nation": nation.pk}, files={})

    assert not form.is_valid()


@pytest.mark.django_db
def test_admin_form_rejects_oversized_flag(draft_variant_for_primary):
    nation = draft_variant_for_primary.nations.first()
    oversized = "<svg>" + "a" * (FLAG_MAX_BYTES + 1) + "</svg>"

    form = NationFlagAdminForm(
        data={"nation": nation.pk}, files={"svg_file": _upload(oversized)}
    )

    assert not form.is_valid()
