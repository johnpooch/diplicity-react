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

COMMITTED_FLAGS = sorted(
    (Path(__file__).resolve().parent.parent / "variant" / "data" / "flags").glob(
        "*/*.svg"
    )
)

SVG_OPEN = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'

UNSAFE_SVG_PAYLOADS = [
    ('<a xlink:href="java&#x09;script:alert(1)"><rect id="kept"/></a>', "alert("),
    ('<animate attributeName="href" values="javascript:alert(1)"/>', "alert("),
    ('<set attributeName="href" from="javascript:alert(1)"/>', "alert("),
    ('<rect onclick="alert(1)" onmouseover="alert(2)"/>', "alert("),
    ("<script>alert(1)</script>", "alert("),
    (
        '<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">alert(1)</div></foreignObject>',
        "alert(",
    ),
    (
        '<html:script xmlns:html="http://www.w3.org/1999/xhtml">alert(1)</html:script>',
        "alert(",
    ),
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
    (
        "<style>@font-face{font-family:'F';src:url(https://evil.example/f.woff)}</style>",
        "evil.example",
    ),
    (
        '<style>.a{fill:url(https://evil.example/a.png)}</style><rect class="a"/>',
        "evil.example",
    ),
    (
        '<style>.a{fill:u\\72l(https://evil.example/a.png)}</style><rect class="a"/>',
        "evil.example",
    ),
    ('<style>.a{fill:expression(alert(1))}</style><rect class="a"/>', "alert("),
    (
        '<style>@import url(https://evil.example/x.css);.a{fill:#fff}</style><rect class="a"/>',
        "evil.example",
    ),
    ('<style>.a{fill:#fff}body{fill:#123456}</style><rect class="a"/>', "#123456"),
    ('<style>.a{fill:#fff}*{fill:#654321}</style><rect class="a"/>', "#654321"),
    ('<style>.a, rect{fill:#abcdef}</style><rect class="a"/>', "#abcdef"),
    ('<style>.a{fill:#fedcba}</style><rect class="a"/>', "<style"),
    ('<style>.a .b{fill:#111111}</style><g class="a"><rect class="b"/></g>', "#111111"),
    ('<style>.a>.b{fill:#222222}</style><g class="a"><rect class="b"/></g>', "#222222"),
    ('<style>rect.a{fill:#333333}</style><rect class="a"/>', "#333333"),
    ('<style>.a:first-child{fill:#444444}</style><rect class="a"/>', "#444444"),
    ('<style>.a[id]{fill:#555555}</style><rect id="r" class="a"/>', "#555555"),
    ('<style>.a.b *{fill:#666666}</style><g class="a b"><rect/></g>', "#666666"),
]

SAFE_SVG_CONTENT = [
    '<use xlink:href="#a"/>',
    '<image xlink:href="data:image/png;base64,iVBORw0KGgo="/>',
    '<rect fill="url(#g)" style="fill:url(#g);stroke:#000"/>',
    "<style>@font-face{font-family:'F';src:url(data:font/woff2;base64,AAAA) format('woff2')}</style>",
    """<style>
@font-face {
  font-family: 'Libre Baskerville';
  font-style: normal;
  font-weight: 700;
  src: url('data:font/woff2;charset=utf-8;base64,AAAA') format('woff2');
  unicode-range: U+2e, U+41-59, U+61-70, U+72-7a, U+4e0a-4e0b, U+1f1e6-1f1ff, U+4??;
}
</style>""",
    '<filter color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="2"/></filter>',
    '<g color-interpolation="sRGB" shape-rendering="crispEdges" text-rendering="geometricPrecision"'
    ' color-rendering="optimizeQuality" image-rendering="optimizeSpeed" overflow="visible"'
    ' enable-background="new" pointer-events="none"/>',
]

INVALID_UNICODE_RANGES = [
    "U+GG",
    "U+1234567",
    "U+0-7F url(https://evil.example/f.woff)",
    "U+0-7F, expression(alert(1))",
    "U+0-7F, 0-7F",
    "U+4?0",
]

CLASS_STYLESHEET = (
    ".cls-1 { fill: #b51f24; }  .cls-2 { fill: #80248e; }\n"
    ".cls-2, .cls-3, .cls-4 { fill: none; stroke: #000; stroke-miterlimit: 10; }"
)

CLASS_STYLED_ELEMENTS = [
    ('class="cls-1"', "fill:#b51f24"),
    ('class="cls-4"', "fill:none;stroke:#000;stroke-miterlimit:10"),
    ('class="cls-2"', "fill:none;stroke:#000;stroke-miterlimit:10"),
    ('class="cls-1 cls-3"', "fill:none;stroke:#000;stroke-miterlimit:10"),
    ('class="cls-1" style="fill:#fff"', "fill:#fff"),
    ('class="cls-3" style="stroke:#fff"', "fill:none;stroke-miterlimit:10;stroke:#fff"),
]

COMPOUND_CLASS_STYLESHEET = (
    ".owner-Stark.sc{fill:#6f8190}.sc{fill:#fffaf0;stroke-width:1.9}"
    ".border.land,.border.sea{stroke:#3d3226;stroke-width:1.1}.coast,.border.sea{stroke-dasharray:5 3}"
)

COMPOUND_CLASS_STYLED_ELEMENTS = [
    ('class="sc owner-Stark"', ' style="fill:#6f8190;stroke-width:1.9"'),
    ('class="owner-Stark"', ""),
    (
        'class="border sea"',
        ' style="stroke:#3d3226;stroke-width:1.1;stroke-dasharray:5 3"',
    ),
    ('class="border"', ""),
    ('class="coast"', ' style="stroke-dasharray:5 3"'),
    ('class="sc owner-Stark" style="fill:#000"', ' style="stroke-width:1.9;fill:#000"'),
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
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_to_published_variant_forbidden(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
        minimal_flag_svg,
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
            reverse(
                "nation-flag",
                kwargs={"variant_id": "secondary-draft", "nation_id": "greens"},
            ),
            _flag_upload(minimal_flag_svg),
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_own_draft_flag_success(
        self, authenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
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
        url = reverse(
            "nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}
        )
        first = authenticated_client.put(
            url, _flag_upload(minimal_flag_svg), format="multipart"
        )
        second_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 5 5"/>'
        second = authenticated_client.put(
            url, _flag_upload(second_svg), format="multipart"
        )
        assert first.status_code == second.status_code == status.HTTP_200_OK
        assert first.data["flag_url"] != second.data["flag_url"]
        assert (
            NationFlag.objects.filter(
                nation__variant_id="primary-draft", nation__nation_id="reds"
            ).count()
            == 1
        )

    def test_upload_rejects_oversize(
        self, authenticated_client, draft_variant_for_primary
    ):
        huge = (
            '<svg xmlns="http://www.w3.org/2000/svg">' + ("<rect/>" * 50000) + "</svg>"
        )
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(huge),
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_rejects_malformed_svg(
        self, authenticated_client, draft_variant_for_primary
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload("<svg><rect"),
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_sanitizes_scripts(
        self, authenticated_client, draft_variant_for_primary
    ):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<script>alert(1)</script><rect id="r1" onclick="x"/>'
            "</svg>"
        )
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
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
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
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
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(f"{SVG_OPEN}{content}</svg>"),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert content in served

    @pytest.mark.parametrize("unicode_range", INVALID_UNICODE_RANGES)
    def test_upload_drops_font_face_with_invalid_unicode_range(
        self, authenticated_client, draft_variant_for_primary, unicode_range
    ):
        valid = "@font-face{font-family:'A';src:url(data:font/woff2;base64,AAAA) format('woff2');unicode-range:U+0-7F}"
        invalid = f"@font-face{{font-family:'B';src:url(data:font/woff2;base64,AAAA);unicode-range:{unicode_range}}}"
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(f"{SVG_OPEN}<style>{valid}{invalid}</style></svg>"),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert f"<style>{valid}</style>" in served

    @pytest.mark.parametrize("attributes, expected_style", CLASS_STYLED_ELEMENTS)
    def test_upload_inlines_class_rules(
        self,
        authenticated_client,
        draft_variant_for_primary,
        attributes,
        expected_style,
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(
                f'{SVG_OPEN}<style>{CLASS_STYLESHEET}</style><rect id="target" {attributes}/></svg>'
            ),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert f'<rect id="target" style="{expected_style}"/>' in served
        assert "class=" not in served
        assert "<style" not in served

    @pytest.mark.parametrize(
        "attributes, expected_attributes", COMPOUND_CLASS_STYLED_ELEMENTS
    )
    def test_upload_inlines_compound_class_rules_by_specificity(
        self,
        authenticated_client,
        draft_variant_for_primary,
        attributes,
        expected_attributes,
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(
                f'{SVG_OPEN}<style>{COMPOUND_CLASS_STYLESHEET}</style><rect id="target" {attributes}/></svg>'
            ),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert f'<rect id="target"{expected_attributes}/>' in served
        assert "class=" not in served
        assert "<style" not in served

    def test_upload_keeps_font_faces_and_inlines_class_rules_from_one_stylesheet(
        self, authenticated_client, draft_variant_for_primary
    ):
        font_face = "@font-face{font-family:'F';src:url(data:font/woff2;base64,AAAA) format('woff2')}"
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload(
                f"{SVG_OPEN}<style>.st0{{fill:#FEC50C;}}{font_face}.st1{{fill:#FFFFFF;}}</style>"
                '<rect id="a" class="st0"/><rect id="b" class="st1"/></svg>'
            ),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

        served = authenticated_client.get(response.data["flag_url"]).content.decode()
        assert f"<style>{font_face}</style>" in served
        assert '<rect id="a" style="fill:#FEC50C"/>' in served
        assert '<rect id="b" style="fill:#FFFFFF"/>' in served
        assert "class=" not in served

    def test_upload_rejects_non_svg_root(
        self, authenticated_client, draft_variant_for_primary
    ):
        response = authenticated_client.put(
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
            _flag_upload('<html xmlns="http://www.w3.org/1999/xhtml"><body/></html>'),
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "flag": "Flag must be an <svg> element in the SVG namespace."
        }

    def test_reuploading_a_served_flag_keeps_its_url(
        self, authenticated_client, draft_variant_for_primary
    ):
        url = reverse(
            "nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}
        )
        first = authenticated_client.put(
            url, _flag_upload(COMMITTED_FLAGS[0].read_text()), format="multipart"
        )
        served = authenticated_client.get(first.data["flag_url"]).content.decode()

        second = authenticated_client.put(url, _flag_upload(served), format="multipart")

        assert second.data["flag_url"] == first.data["flag_url"]

    def test_delete_flag(
        self, authenticated_client, draft_variant_for_primary, minimal_flag_svg
    ):
        url = reverse(
            "nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}
        )
        authenticated_client.put(
            url, _flag_upload(minimal_flag_svg), format="multipart"
        )
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
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "nonexistent"},
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
            reverse(
                "nation-flag",
                kwargs={"variant_id": "primary-draft", "nation_id": "reds"},
            ),
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

    def test_sets_locked_down_content_security_policy(
        self, unauthenticated_client, primary_flag
    ):
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
        assert response["Content-Security-Policy"] == (
            "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:"
        )

    def test_gzip_encoded_when_client_accepts(
        self, unauthenticated_client, draft_variant_for_primary
    ):
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

    @pytest.mark.parametrize(
        "flag_path", COMMITTED_FLAGS, ids=lambda path: f"{path.parent.name}/{path.stem}"
    )
    def test_committed_flags_keep_their_rendering(
        self,
        authenticated_client,
        unauthenticated_client,
        svg_rendering_signature,
        flag_path,
    ):
        variant = authenticated_client.get(
            reverse("variant-detail", kwargs={"pk": flag_path.parent.name})
        )
        nation = next(
            nation
            for nation in variant.data["nations"]
            if nation["nation_id"] == flag_path.stem
        )

        served = unauthenticated_client.get(nation["flag_url"])

        assert served.status_code == status.HTTP_200_OK
        assert svg_rendering_signature(
            served.content.decode()
        ) == svg_rendering_signature(flag_path.read_text())


@pytest.mark.django_db
class TestNationFlagAdminForm:
    def test_admin_form_accepts_valid_upload(
        self, draft_variant_for_primary, minimal_flag_svg
    ):
        nation = draft_variant_for_primary.nations.first()

        form = NationFlagAdminForm(
            data={"nation": nation.pk},
            files={"svg_file": _admin_upload(minimal_flag_svg)},
        )

        assert form.is_valid(), form.errors
        instance = form.save()
        assert instance.nation == nation
        assert (
            instance.content_hash == hashlib.sha256(instance.svg.encode()).hexdigest()
        )

    def test_admin_form_replaces_existing_flag(
        self, draft_variant_for_primary, minimal_flag_svg
    ):
        nation = draft_variant_for_primary.nations.first()
        existing = NationFlag.objects.create(
            nation=nation, svg='<svg xmlns="http://www.w3.org/2000/svg"/>'
        )
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
            data={"nation": nation.pk},
            files={"svg_file": _admin_upload("<svg><g></svg>")},
        )

        assert not form.is_valid()

    def test_admin_form_rejects_non_svg_root(self, draft_variant_for_primary):
        nation = draft_variant_for_primary.nations.first()

        form = NationFlagAdminForm(
            data={"nation": nation.pk},
            files={
                "svg_file": _admin_upload(
                    '<html xmlns="http://www.w3.org/1999/xhtml"/>'
                )
            },
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
