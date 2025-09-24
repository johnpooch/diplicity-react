import pytest
from django.urls import reverse
from rest_framework import status

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

    classical_variant_data = next(
        (v for v in response.data if v["id"] == classical_variant.id), None
    )
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