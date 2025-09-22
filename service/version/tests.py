import pytest
from django.urls import reverse
from rest_framework import status


class TestVersionRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_version_success(self, authenticated_client):
        url = reverse("version-retrieve")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "environment" in response.data
        assert "version" in response.data
        assert isinstance(response.data["environment"], str)
        assert isinstance(response.data["version"], str)

    @pytest.mark.django_db
    def test_retrieve_version_unauthenticated(self, unauthenticated_client):
        url = reverse("version-retrieve")
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "environment" in response.data
        assert "version" in response.data
        assert isinstance(response.data["environment"], str)
        assert isinstance(response.data["version"], str)
