import copy
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status

from variant.models import Variant
from variant.utils import variant_to_canonical_dict


@pytest.fixture
def classical_dvar(classical_variant):
    return variant_to_canonical_dict(classical_variant)


@pytest.fixture
def classical_dsvg(classical_variant):
    return classical_variant.svg.svg


def _dvar_upload(dvar, dsvg):
    return {
        "dvar": SimpleUploadedFile("upload.dvar.json", json.dumps(dvar).encode(), "application/json"),
        "dsvg": SimpleUploadedFile("upload.svg", dsvg.encode(), "image/svg+xml"),
    }


def _list_query_count(client):
    connection.queries_log.clear()
    with override_settings(DEBUG=True):
        response = client.get(reverse("variant-list"))
    assert response.status_code == status.HTTP_200_OK
    return len(connection.queries), response


@pytest.mark.django_db
def test_list_variants_baseline_query_count(authenticated_client):
    """Snapshot guard for the absolute query count of GET /variants/. The two
    published variants (classical, italy-vs-germany) are seeded by migration.
    If this number grows, something added an un-prefetched relation access."""
    query_count, response = _list_query_count(authenticated_client)
    assert len(response.data) >= 2
    assert query_count <= 20, f"GET /variants/ issued {query_count} queries for {len(response.data)} variants"


@pytest.mark.django_db
def test_list_variants_no_n_plus_one_when_variant_count_grows(
    authenticated_client, classical_dvar, classical_dsvg
):
    """Adding a third variant must not increase the per-request query count.
    Regression guard for the variants/ slowdown observed in production
    (P50 ~50ms → ~600ms over April–May 2026)."""
    baseline_count, baseline_response = _list_query_count(authenticated_client)
    baseline_variant_count = len(baseline_response.data)

    extra = copy.deepcopy(classical_dvar)
    extra["id"] = "n-plus-one-probe"
    extra["name"] = "N+1 Probe"
    upload_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(extra, classical_dsvg),
        format="multipart",
    )
    assert upload_response.status_code == status.HTTP_201_CREATED, upload_response.data
    assert Variant.objects.filter(id="n-plus-one-probe").exists()

    grown_count, grown_response = _list_query_count(authenticated_client)
    assert len(grown_response.data) == baseline_variant_count + 1
    assert grown_count == baseline_count, (
        f"Query count scaled with variants: {baseline_count} for "
        f"{baseline_variant_count} variants vs {grown_count} for "
        f"{baseline_variant_count + 1} variants"
    )


@pytest.mark.django_db
def test_list_variants_returns_etag_and_cache_control(authenticated_client):
    response = authenticated_client.get(reverse("variant-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response["ETag"].startswith('"') and response["ETag"].endswith('"')
    assert "max-age=60" in response["Cache-Control"]
    assert "must-revalidate" in response["Cache-Control"]


@pytest.mark.django_db
def test_list_variants_returns_304_on_matching_if_none_match(authenticated_client):
    first = authenticated_client.get(reverse("variant-list"))
    etag = first["ETag"]

    second = authenticated_client.get(reverse("variant-list"), HTTP_IF_NONE_MATCH=etag)
    assert second.status_code == status.HTTP_304_NOT_MODIFIED
    assert second["ETag"] == etag


@pytest.mark.django_db
def test_list_variants_etag_changes_when_a_variant_is_uploaded(
    authenticated_client, classical_dvar, classical_dsvg
):
    initial = authenticated_client.get(reverse("variant-list"))
    initial_etag = initial["ETag"]

    extra = copy.deepcopy(classical_dvar)
    extra["id"] = "etag-probe"
    extra["name"] = "ETag Probe"
    upload = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(extra, classical_dsvg),
        format="multipart",
    )
    assert upload.status_code == status.HTTP_201_CREATED, upload.data

    after = authenticated_client.get(
        reverse("variant-list"), HTTP_IF_NONE_MATCH=initial_etag
    )
    assert after.status_code == status.HTTP_200_OK
    assert after["ETag"] != initial_etag
