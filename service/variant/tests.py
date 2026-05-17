import pytest
from common.constants import PhaseStatus
from phase.models import Phase
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from rest_framework import status

from variant.models import Variant, default_phase_progression

viewname = "variant-list"


@pytest.mark.django_db
def test_list_variants_success(authenticated_client, classical_variant):
    url = reverse(viewname)
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 6

    variants_by_id = {v["id"]: v for v in response.data}
    assert variants_by_id[classical_variant.id]["name"] == classical_variant.name
    assert variants_by_id["italy-vs-germany"]["name"] == "Italy vs Germany"

    classical_variant_data = variants_by_id[classical_variant.id]

    assert "rules" in classical_variant_data
    assert classical_variant_data["rules"].startswith("The first to 18 Supply Centers")

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
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_list_variants_includes_svg_url(authenticated_client):
    response = authenticated_client.get(reverse(viewname))

    classical = {v["id"]: v for v in response.data}["classical"]
    assert classical["svg_url"] is not None
    assert "/variants/classical/svg/" in classical["svg_url"]
    assert classical["svg_url"].endswith(".svg")


@pytest.mark.django_db
def test_svg_url_is_null_when_variant_has_no_svg(authenticated_client):
    Variant.objects.create(id="no-svg", name="No SVG", description="", author="")

    response = authenticated_client.get(reverse(viewname))

    no_svg = {v["id"]: v for v in response.data}["no-svg"]
    assert no_svg["svg_url"] is None


class TestVariantListViewQueryPerformance:

    @pytest.mark.django_db
    def test_list_variants_query_count_with_all_variants(self, authenticated_client, classical_variant):
        """Test query count when listing all variants (classical + italy-vs-germany)."""
        url = reverse(viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 6

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
        # Should have at least 4 variants now (classical, hundred, italy-vs-germany, youngstown-redux, test-single-variant)
        assert len(response.data) >= 5

        # Should have the same number of queries regardless of variant count
        # due to prefetch_related optimization
        query_count = len(connection.queries)
        assert query_count == 16


class TestPhaseProgressionBackfill:

    @pytest.mark.django_db
    def test_classical_phase_progression(self, classical_variant):
        assert classical_variant.phase_progression == default_phase_progression()

    @pytest.mark.django_db
    def test_hundred_phase_progression(self, hundred_variant):
        progression = hundred_variant.phase_progression
        assert progression["seasons"] == ["Year"]

        adjustment_to_movement = next(
            t for t in progression["transitions"]
            if t["from"]["type"] == "Adjustment"
        )
        assert adjustment_to_movement["to"]["type"] == "Movement"
        assert adjustment_to_movement["to"]["yearDelta"] == 5

    @pytest.mark.django_db
    def test_every_variant_has_phase_progression(self, classical_variant):
        assert not Variant.objects.filter(phase_progression={}).exists()
        for variant in Variant.objects.all():
            assert variant.phase_progression["seasons"]
            assert variant.phase_progression["transitions"]


class TestRulesBackfill:

    @pytest.mark.django_db
    def test_classical_rules(self, classical_variant):
        assert classical_variant.rules == (
            "The first to 18 Supply Centers (SC) is the winner.\n"
            "Kiel and Constantinople have a canal, so fleets can exit on either side.\n"
            "Armies can move from Denmark to Kiel."
        )

    @pytest.mark.django_db
    def test_hundred_rules(self, hundred_variant):
        assert hundred_variant.rules.startswith(
            "First to 9 Supply Centers (SC) is the winner."
        )

    @pytest.mark.django_db
    def test_every_in_db_variant_has_rules(self, classical_variant):
        in_db_ids = {
            "classical", "italy-vs-germany", "hundred",
            "youngstown-redux", "vietnam-war", "canton",
        }
        for variant in Variant.objects.filter(id__in=in_db_ids):
            assert variant.rules
