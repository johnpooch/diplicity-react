import pytest
from common.constants import PhaseStatus
from phase.models import Phase
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from rest_framework import status

from variant.models import Variant

viewname = "variant-list"


@pytest.mark.django_db
def test_list_variants_success(authenticated_client, classical_variant):
    url = reverse(viewname)
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]["id"] == classical_variant.id
    assert response.data[0]["name"] == classical_variant.name
    assert response.data[1]["id"] == "italy-vs-germany"
    assert response.data[1]["name"] == "Italy vs Germany"

    classical_variant_data = next((v for v in response.data if v["id"] == classical_variant.id), None)
    assert classical_variant_data is not None

    assert "template_phase" in classical_variant_data
    template_phase = classical_variant_data["template_phase"]

    assert "season" in template_phase
    assert "year" in template_phase
    assert "type" in template_phase
    assert "units" in template_phase
    assert "supply_centers" in template_phase
    assert isinstance(template_phase["units"], list)
    assert isinstance(template_phase["supply_centers"], list)

    # Check that we have the expected number of units and supply centers
    assert len(template_phase["units"]) > 0
    assert len(template_phase["supply_centers"]) > 0


@pytest.mark.django_db
def test_list_variants_unauthenticated(unauthenticated_client):
    url = reverse(viewname)
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestVariantListViewQueryPerformance:

    @pytest.mark.django_db
    def test_list_variants_query_count_with_all_variants(self, authenticated_client, classical_variant):
        """Test query count when listing all variants (classical + italy-vs-germany)."""
        url = reverse(viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # With optimized queries, we should have a constant number of queries
        # regardless of the number of variants due to prefetch_related
        query_count = len(connection.queries)

        assert query_count == 16

    @pytest.mark.django_db
    def test_list_variants_query_count_with_single_variant(self, authenticated_client, classical_variant):
        """Test query count when only one variant exists (by creating a fresh test)."""
        # Create a new variant to test with a single variant scenario

        # Create a minimal test variant
        test_variant = Variant.objects.create(
            id="test-single-variant",
            name="Test Single Variant",
            description="A test variant for query optimization testing",
            author="Test",
        )

        # Create a template phase for the test variant
        Phase.objects.create(
            variant=test_variant, season="Spring", year=1901, type="Movement", status=PhaseStatus.TEMPLATE, ordinal=1
        )

        url = reverse(viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should have at least 3 variants now (classical, italy-vs-germany, test-single-variant)
        assert len(response.data) >= 3

        # Should have the same number of queries regardless of variant count
        # due to prefetch_related optimization
        query_count = len(connection.queries)
        assert query_count == 16
