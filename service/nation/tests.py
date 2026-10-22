import gzip
import hashlib
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from nation.admin import NationFlagAdminForm
from nation.models import NationFlag
from nation.utils import FLAG_MAX_BYTES


COMMITTED_FLAGS = sorted((Path(__file__).resolve().parent.parent / "variant" / "data" / "flags").glob("*/*.svg"))

SVG_OPEN = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'

UNSAFE_SVG_PAYLOADS = [
    ('<a xlink:href="java&#x09;script:alert(1)"><rect id="kept"/></a>', "alert("),
    ('<animate attributeName="href" values="javascript:alert(1)"/>', "alert("),
    ('<set attributeName="href" from="javascript:alert(1)"/>', "alert("),
    ('<rect onclick="alert(1)" onmouseover="alert(2)"/>', "alert("),
    ("<script>alert(1)</script>", "alert("),
    ('<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">alert(1)</div></foreignObject>', "alert("),
    ('<html:script xmlns:html="http://www.w3.org/1999/xhtml">alert(1)</html:script>', "alert("),
    ('<a href="data:text/html,alert(1)"><rect/></a>', "alert("),
    ('<image href="javascript:alert(1)"/>', "alert("),
    ('<image xlink:href="data:image/svg+xml;base64,PHN2Zy8+"/>', "data:image/svg"),
    ('<use href="https://evil.example/sprite.svg#a"/>', "evil.example"),
    ('<rect fill="url(https://evil.example/a.png)"/>', "evil.example"),
    ('<rect style="fill:url(https://evil.example/a.png)"/>', "evil.example"),
    ('<rect style="fill:u\\72l(https://evil.example/a.png)"/>', "evil.example"),
    ('<rect style="width:expression(alert(1))"/>', "alert("),
    ("<style>@import url(https://evil.example/x.css);</style>", "evil.example"),
    ("<style>rect{fill:url(https://evil.example/a.png)}</style>", "evil.example"),
    ("<style>@font-face{font-family:'F';src:url(https://evil.example/f.woff)}</style>", "evil.example"),
]

SAFE_SVG_CONTENT = [
    '<use xlink:href="#a"/>',
    '<image xlink:href="data:image/png;base64,iVBORw0KGgo="/>',
    '<rect fill="url(#g)" style="fill:url(#g);stroke:#000"/>',
    "<style>@font-face{font-family:'F';src:url(data:font/woff2;base64,AAAA) format('woff2')}</style>",
]


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

    @pytest.mark.parametrize("payload, marker", UNSAFE_SVG_PAYLOADS)
    def test_upload_removes_unsafe_content(
        self, authenticated_client, draft_variant_for_primary, payload, marker
    ):
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(f'{SVG_OPEN}<rect id="sentinel"/>{payload}</svg>'),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert marker not in served
        assert 'id="sentinel"' in served

    @pytest.mark.parametrize("content", SAFE_SVG_CONTENT)
    def test_upload_keeps_same_document_references(
        self, authenticated_client, draft_variant_for_primary, content
    ):
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload(f"{SVG_OPEN}{content}</svg>"),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert content in served

    def test_upload_rejects_non_svg_root(self, authenticated_client, draft_variant_for_primary):
        response = authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
            _flag_upload('<html xmlns="http://www.w3.org/1999/xhtml"><body/></html>'),
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"flag": "Flag must be an <svg> element in the SVG namespace."}

    def test_reuploading_a_served_flag_keeps_its_url(
        self, authenticated_client, draft_variant_for_primary
    ):
        url = reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"})
        first = authenticated_client.put(
            url, _flag_upload(COMMITTED_FLAGS[0].read_text()), format="multipart"
        )
        served = authenticated_client.get(first.data["flag_url"]).content.decode()

        second = authenticated_client.put(url, _flag_upload(served), format="multipart")

        assert second.data["flag_url"] == first.data["flag_url"]

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

    def test_gzip_encoded_when_client_accepts(self, unauthenticated_client, draft_variant_for_primary):
        stripes = "".join(
            f'<rect y="{i}" width="10" height="1" fill="#ff0000"/>' for i in range(10)
        )
        flag = NationFlag.objects.create(
            nation=draft_variant_for_primary.nations.get(nation_id="reds"),
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">{stripes}</svg>',
        )
        response = unauthenticated_client.get(
            reverse(
                "nation-flag-svg",
                kwargs={
                    "variant_id": "primary-draft",
                    "nation_id": "reds",
                    "content_hash": flag.content_hash,
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


    @pytest.mark.parametrize("flag_path", COMMITTED_FLAGS, ids=lambda path: f"{path.parent.name}/{path.stem}")
    def test_committed_flags_keep_their_rendering(
        self, authenticated_client, unauthenticated_client, svg_rendering_signature, flag_path
    ):
        variant = authenticated_client.get(reverse("variant-detail", kwargs={"pk": flag_path.parent.name}))
        nation = next(nation for nation in variant.data["nations"] if nation["nation_id"] == flag_path.stem)

        served = unauthenticated_client.get(nation["flag_url"])

        assert served.status_code == status.HTTP_200_OK
        assert svg_rendering_signature(served.content.decode()) == svg_rendering_signature(flag_path.read_text())


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
        existing = NationFlag.objects.create(nation=nation, svg='<svg xmlns="http://www.w3.org/2000/svg"/>')
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

    def test_admin_form_rejects_non_svg_root(self, draft_variant_for_primary):
        nation = draft_variant_for_primary.nations.first()

        form = NationFlagAdminForm(
            data={"nation": nation.pk},
            files={"svg_file": _admin_upload('<html xmlns="http://www.w3.org/1999/xhtml"/>')},
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
