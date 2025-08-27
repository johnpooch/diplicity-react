import pytest
from django.urls import reverse
from rest_framework import status

viewname = "variant-list"

@pytest.mark.django_db
def test_list_variants_success(authenticated_client, classical_variant):
    """
    Test that an authenticated user can successfully list variants.
    """
    url = reverse(viewname)
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]["id"] == classical_variant.id
    assert response.data[0]["name"] == classical_variant.name
    assert response.data[1]["id"] == "italy-vs-germany"
    assert response.data[1]["name"] == "Italy vs Germany"

@pytest.mark.django_db
def test_list_variants_unauthenticated(unauthenticated_client):
    """
    Test that unauthenticated users cannot list variants.
    """
    url = reverse(viewname)
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_variant_initial_phase_field(authenticated_client, classical_variant):
    """
    Test that the initial_phase field is properly included in variant responses.
    """
    url = reverse(viewname)
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    
    # Find the classical variant in the response
    classical_variant_data = next(
        (v for v in response.data if v["id"] == classical_variant.id), None
    )
    assert classical_variant_data is not None
    
    # Check that initial_phase field exists and has the expected structure
    assert "initial_phase" in classical_variant_data
    initial_phase = classical_variant_data["initial_phase"]
    
    # Check basic phase fields
    assert initial_phase["id"] == 0
    assert initial_phase["ordinal"] == 1
    assert initial_phase["season"] == classical_variant.start["season"]
    assert initial_phase["year"] == classical_variant.start["year"]
    assert initial_phase["type"] == classical_variant.start["type"]
    assert initial_phase["status"] == "pending"
    
    # Check that units and supply centers are properly converted
    assert "units" in initial_phase
    assert "supply_centers" in initial_phase
    assert isinstance(initial_phase["units"], list)
    assert isinstance(initial_phase["supply_centers"], list) 