import pytest
from django.urls import reverse
from rest_framework import status


class TestHealthCheckView:
    """Test the health check endpoint functionality."""

    @pytest.mark.django_db
    def test_health_check_returns_ok(self, unauthenticated_client):
        """Test that the health check endpoint returns 200 OK with 'ok' response."""
        url = reverse("health-check")
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b"ok"

    @pytest.mark.django_db
    def test_health_check_works_without_authentication(self, unauthenticated_client):
        """Test that the health check endpoint works without authentication."""
        url = reverse("health-check")
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_health_check_bypasses_csrf(self, unauthenticated_client):
        """Test that the health check endpoint bypasses CSRF protection."""
        url = reverse("health-check")
        # POST request without CSRF token should still work due to @csrf_exempt
        response = unauthenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b"ok"

    @pytest.mark.django_db
    def test_health_check_with_different_methods(self, unauthenticated_client):
        """Test that the health check endpoint works with different HTTP methods."""
        url = reverse("health-check")

        # Test GET
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Test POST
        response = unauthenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        # Test HEAD
        response = unauthenticated_client.head(url)
        assert response.status_code == status.HTTP_200_OK
