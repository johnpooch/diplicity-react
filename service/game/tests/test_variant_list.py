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