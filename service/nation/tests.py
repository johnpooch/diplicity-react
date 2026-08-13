import gzip
import hashlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from nation.admin import NationFlagAdminForm
from nation.models import NationFlag
from nation.utils import FLAG_MAX_BYTES


def _flag_upload(svg, filename="flag.svg"):
    return {"flag": SimpleUploadedFile(filename, svg.encode(), "image/svg+xml")}


def _admin_upload(svg, name="flag.svg"):
    return SimpleUploadedFile(name, svg.encode(), content_type="image/svg+xml")


@pytest.mark.django_db
class TestNationFlagUploadView:
    def test_upload_requires_authentication(
        self, unauthenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        response = unauthenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_to_published_variant_forbidden(
        self, authenticated_client, classical_variant, classical_england_nation, minimal_flag_svg
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={
                    "variant_id": "classical",
                    "nation_id": classical_england_nation.nation_id,
                },
            ),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_to_other_users_draft_forbidden(
        self, authenticated_client, draft_variant_for_secondary, minimal_flag_svg
    ):
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "secondary-draft", "nation_id": "greens"}),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_own_draft_flag_success(
        self, authenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["nation_id"] == "reds"
        assert response.data["flag_url"] is not None
        assert NationFlag.objects.filter(
            nation__variant_id="primary-draft", nation__nation_id="reds"
        ).exists()

    def test_upload_replaces_existing_flag(
        self, authenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        url = reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"})
        first = authenticated_client.put(url, _flag_upload(minimal_flag_svg), format="multipart")
        second_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 5 5"/>'
        second = authenticated_client.put(url, _flag_upload(second_svg), format="multipart")
        assert first.status_code == second.status_code == status.HTTP_200_OK
        assert first.data["flag_url"] != second.data["flag_url"]
        assert (
            NationFlag.objects.filter(
                nation__variant_id="primary-draft", nation__nation_id="reds"
            ).count()
            == 1
        )

    def test_upload_rejects_oversize(self, authenticated_client, draft_variant_for_primary):
        huge = '<svg xmlns="http://www.w3.org/2000/svg">' + ("<rect/>" * 50000) + "</svg>"
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(huge),
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_rejects_malformed_svg(self, authenticated_client, draft_variant_for_primary):
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload("<svg><rect"),
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_sanitizes_scripts(self, authenticated_client, draft_variant_for_primary):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<script>alert(1)</script><rect id="r1" onclick="x"/>'
            "</svg>"
        )
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        flag = NationFlag.objects.get(
            nation__variant_id="primary-draft", nation__nation_id="reds"
        )
        assert "<script" not in flag.svg
        assert "onclick" not in flag.svg
        assert 'id="r1"' in flag.svg

    def test_delete_flag(self, authenticated_client, draft_variant_for_primary, minimal_flag_svg):
        url = reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"})
        authenticated_client.put(url, _flag_upload(minimal_flag_svg), format="multipart")
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not NationFlag.objects.filter(
            nation__variant_id="primary-draft", nation__nation_id="reds"
        ).exists()

    def test_unknown_nation_returns_404(
        self, authenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "nonexistent"}
            ),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_flag_upload_changes_variant_detail_etag(
        self, authenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        detail_url = reverse("variant-detail", kwargs={"pk": "primary-draft"})
        before = authenticated_client.get(detail_url)
        etag = before["ETag"]

        authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )

        after = authenticated_client.get(detail_url, HTTP_IF_NONE_MATCH=etag)
        assert after.status_code == status.HTTP_200_OK
        assert after["ETag"] != etag


@pytest.mark.django_db
class TestNationFlagSvgView:
    def test_serves_svg_for_a_valid_hash(self, unauthenticated_client, primary_flag):
        response = unauthenticated_client.get(
            reverse(
                "nation-flag-svg",
                kwargs={
                    "variant_id": "primary-draft",
                    "nation_id": "reds",
                    "content_hash": primary_flag.content_hash,
                },
            )
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "image/svg+xml"

    def test_sets_immutable_cache_control(self, unauthenticated_client, primary_flag):
        response = unauthenticated_client.get(
            reverse(
                "nation-flag-svg",
                kwargs={
                    "variant_id": "primary-draft",
                    "nation_id": "reds",
                    "content_hash": primary_flag.content_hash,
                },
            )
        )
        assert "immutable" in response["Cache-Control"]
        assert "max-age=31536000" in response["Cache-Control"]

    def test_gzip_encoded_when_client_accepts(self, unauthenticated_client, primary_flag):
        response = unauthenticated_client.get(
            reverse(
                "nation-flag-svg",
                kwargs={
                    "variant_id": "primary-draft",
                    "nation_id": "reds",
                    "content_hash": primary_flag.content_hash,
                },
            ),
            HTTP_ACCEPT_ENCODING="gzip",
        )
        assert response["Content-Encoding"] == "gzip"
        decompressed = gzip.decompress(response.content).decode()
        assert "<svg" in decompressed

    def test_unknown_hash_returns_404(self, unauthenticated_client, primary_flag):
        response = unauthenticated_client.get(
            reverse(
                "nation-flag-svg",
                kwargs={
                    "variant_id": "primary-draft",
                    "nation_id": "reds",
                    "content_hash": "x" * 64,
                },
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unknown_nation_returns_404(self, unauthenticated_client, primary_flag):
        response = unauthenticated_client.get(
            reverse(
                "nation-flag-svg",
                kwargs={
                    "variant_id": "primary-draft",
                    "nation_id": "nope",
                    "content_hash": primary_flag.content_hash,
                },
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestNationFlagAdminForm:
    def test_admin_form_accepts_valid_upload(self, draft_variant_for_primary, minimal_flag_svg):
        nation = draft_variant_for_primary.nations.first()

        form = NationFlagAdminForm(
            data={"nation": nation.pk}, files={"svg_file": _admin_upload(minimal_flag_svg)}
        )

        assert form.is_valid(), form.errors
        instance = form.save()
        assert instance.nation == nation
        assert instance.content_hash == hashlib.sha256(instance.svg.encode()).hexdigest()

    def test_admin_form_replaces_existing_flag(self, draft_variant_for_primary, minimal_flag_svg):
        nation = draft_variant_for_primary.nations.first()
        existing = NationFlag.objects.create(nation=nation, svg="<svg/>")
        original_hash = existing.content_hash

        form = NationFlagAdminForm(
            data={"nation": nation.pk},
            files={"svg_file": _admin_upload(minimal_flag_svg)},
            instance=existing,
        )

        assert form.is_valid(), form.errors
        instance = form.save()
        assert instance.content_hash != original_hash

    def test_admin_form_rejects_malformed_xml(self, draft_variant_for_primary):
        nation = draft_variant_for_primary.nations.first()

        form = NationFlagAdminForm(
            data={"nation": nation.pk}, files={"svg_file": _admin_upload("<svg><g></svg>")}
        )

        assert not form.is_valid()

    def test_admin_form_requires_a_file_on_add(self, draft_variant_for_primary):
        nation = draft_variant_for_primary.nations.first()

        form = NationFlagAdminForm(data={"nation": nation.pk}, files={})

        assert not form.is_valid()

    def test_admin_form_rejects_oversized_flag(self, draft_variant_for_primary):
        nation = draft_variant_for_primary.nations.first()
        oversized = "<svg>" + "a" * (FLAG_MAX_BYTES + 1) + "</svg>"

        form = NationFlagAdminForm(
            data={"nation": nation.pk}, files={"svg_file": _admin_upload(oversized)}
        )

        assert not form.is_valid()
