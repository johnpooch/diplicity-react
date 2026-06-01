import gzip

import pytest
from django.urls import reverse
from rest_framework import status

from nation.models import NationFlag


@pytest.fixture
def primary_flag(db, draft_variant_for_primary, minimal_flag_svg):
    nation = draft_variant_for_primary.nations.get(nation_id="reds")
    return NationFlag.objects.create(nation=nation, svg=minimal_flag_svg)


@pytest.mark.django_db
def test_serves_svg_for_a_valid_hash(unauthenticated_client, primary_flag):
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


@pytest.mark.django_db
def test_sets_immutable_cache_control(unauthenticated_client, primary_flag):
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


@pytest.mark.django_db
def test_gzip_encoded_when_client_accepts(unauthenticated_client, primary_flag):
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


@pytest.mark.django_db
def test_unknown_hash_returns_404(unauthenticated_client, primary_flag):
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


@pytest.mark.django_db
def test_unknown_nation_returns_404(unauthenticated_client, primary_flag):
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
