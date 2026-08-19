import pytest
from django.test.utils import override_settings
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
        assert "minimum_client_version" in response.data
        assert isinstance(response.data["environment"], str)
        assert isinstance(response.data["version"], str)
        assert isinstance(response.data["minimum_client_version"], str)

    @pytest.mark.django_db
    def test_retrieve_version_unauthenticated(self, unauthenticated_client):
        url = reverse("version-retrieve")
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "environment" in response.data
        assert "version" in response.data
        assert "minimum_client_version" in response.data
        assert isinstance(response.data["environment"], str)
        assert isinstance(response.data["version"], str)
        assert isinstance(response.data["minimum_client_version"], str)

    @pytest.mark.django_db
    def test_retrieve_minimum_client_version_reflects_setting(self, unauthenticated_client):
        url = reverse("version-retrieve")
        with override_settings(MINIMUM_CLIENT_VERSION="1.6.0"):
            response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["minimum_client_version"] == "1.6.0"

    @pytest.mark.django_db
    def test_retrieve_minimum_client_version_defaults_to_gate_disabled(self, unauthenticated_client):
        url = reverse("version-retrieve")
        response = unauthenticated_client.get(url)
        assert response.data["minimum_client_version"] == "0.0.0"
