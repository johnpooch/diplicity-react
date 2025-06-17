import pytest
from django.urls import reverse
from rest_framework import status

viewname = "version-retrieve"

@pytest.mark.django_db
def test_retrieve_version_success(authenticated_client):
    """
    Test that version information can be successfully retrieved.
    """
    url = reverse(viewname)
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert "environment" in response.data
    assert "version" in response.data
    assert isinstance(response.data["environment"], str)
    assert isinstance(response.data["version"], str)

@pytest.mark.django_db
def test_retrieve_version_unauthenticated(unauthenticated_client):
    """
    Test that version information can be retrieved without authentication.
    """
    url = reverse(viewname)
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert "environment" in response.data
    assert "version" in response.data
    assert isinstance(response.data["environment"], str)
    assert isinstance(response.data["version"], str) 