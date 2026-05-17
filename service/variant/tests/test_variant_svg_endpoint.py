import gzip

import pytest

from variant.models import VariantSvg


def _url(variant_id, content_hash):
    return f"/variants/{variant_id}/svg/{content_hash}.svg"


@pytest.mark.django_db
def test_serves_svg_for_a_valid_hash(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("classical", variant_svg.content_hash))

    assert response.status_code == 200
    assert response["Content-Type"] == "image/svg+xml"


@pytest.mark.django_db
def test_sets_immutable_cache_control(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("classical", variant_svg.content_hash))

    assert response["Cache-Control"] == "public, max-age=31536000, immutable"


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
        _url("classical", variant_svg.content_hash), headers={"Accept-Encoding": "identity"}
    )

    assert "Content-Encoding" not in response
    assert response.content.decode() == variant_svg.svg


@pytest.mark.django_db
def test_unknown_hash_returns_404(client):
    response = client.get(_url("classical", "0" * 64))

    assert response.status_code == 404


@pytest.mark.django_db
def test_unknown_variant_returns_404(client):
    variant_svg = VariantSvg.objects.get(variant_id="classical")

    response = client.get(_url("nonexistent", variant_svg.content_hash))

    assert response.status_code == 404
