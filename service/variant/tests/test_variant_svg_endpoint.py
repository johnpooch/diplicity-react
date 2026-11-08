import gzip

import pytest

from variant.models import VariantSvg


def _url(variant_id, content_hash):
    return f"/variants/{variant_id}/svg/{content_hash}.svg"


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "head"])
@pytest.mark.parametrize(
    "origin",
    [None, "capacitor://localhost", "https://localhost", "https://other.example"],
)
def test_serves_svg_for_a_valid_hash(client, method, origin):
    variant_svg = VariantSvg.objects.get(variant_id="classical")
    headers = {"Origin": origin} if origin else {}

    response = getattr(client, method)(
        _url("classical", variant_svg.content_hash), headers=headers
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "image/svg+xml"
    assert response["Access-Control-Allow-Origin"] == "*"
    assert "Access-Control-Allow-Credentials" not in response


@pytest.mark.django_db
def test_sets_immutable_cache_control(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("classical", variant_svg.content_hash))

    assert response["Cache-Control"] == "public, max-age=31536000, immutable"


@pytest.mark.django_db
def test_sets_locked_down_content_security_policy(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("classical", variant_svg.content_hash))

    assert response["Content-Security-Policy"] == (
        "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:"
    )


@pytest.mark.django_db
def test_gzip_encoded_when_client_accepts(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(
        _url("classical", variant_svg.content_hash), headers={"Accept-Encoding": "gzip"}
    )

    assert response["Content-Encoding"] == "gzip"
    assert gzip.decompress(response.content).decode() == variant_svg.svg


@pytest.mark.django_db
def test_uncompressed_when_client_does_not_accept_gzip(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(
        _url("classical", variant_svg.content_hash),
        headers={"Accept-Encoding": "identity"},
    )

    assert "Content-Encoding" not in response
    assert response.content.decode() == variant_svg.svg


@pytest.mark.django_db
def test_stale_hash_redirects_to_current_svg(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("classical", "0" * 64))

    assert response.status_code == 302
    assert response["Location"] == _url("classical", variant_svg.content_hash)
    assert response["Cache-Control"] == "no-cache"


@pytest.mark.django_db
def test_unknown_variant_returns_404(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("nonexistent", variant_svg.content_hash))

    assert response.status_code == 404


@pytest.mark.django_db
def test_variant_without_svg_returns_404(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")
    content_hash = variant_svg.content_hash
    variant_svg.delete()

    response = client.get(_url("classical", content_hash))

    assert response.status_code == 404
