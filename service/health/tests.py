import pytest
from django.urls import reverse
from django.test import RequestFactory, override_settings
from rest_framework import status
from health.middleware import AzureHealthCheckMiddleware
from health.views import health_check


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


class TestAzureHealthCheckMiddleware:
    """Test the Azure health check middleware functionality."""

    def test_middleware_initialization(self):
        """Test that the middleware can be initialized properly."""

        def get_response(request):
            return "response"

        middleware = AzureHealthCheckMiddleware(get_response)
        assert middleware.get_response == get_response

    def test_middleware_passes_through_non_azure_ips(self):
        """Test that the middleware doesn't modify requests from non-Azure IPs."""

        def get_response(request):
            return "response"

        middleware = AzureHealthCheckMiddleware(get_response)
        factory = RequestFactory()

        # Test with localhost
        request = factory.get("/health/", HTTP_HOST="localhost:8000")
        response = middleware(request)
        assert response == "response"
        assert request.META["HTTP_HOST"] == "localhost:8000"

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_middleware_modifies_azure_ips_for_health_check(self):
        """Test that the middleware modifies HTTP_HOST for Azure IPs accessing health check."""

        def get_response(request):
            return "response"

        middleware = AzureHealthCheckMiddleware(get_response)
        factory = RequestFactory()

        # Test with Azure internal IP
        request = factory.get("/health/", HTTP_HOST="169.254.1.1")
        response = middleware(request)
        assert response == "response"
        assert request.META["HTTP_HOST"] == "allowed-health-check"

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_middleware_doesnt_modify_azure_ips_for_non_health_paths(self):
        """Test that the middleware doesn't modify Azure IPs for non-health check paths."""

        def get_response(request):
            return "response"

        middleware = AzureHealthCheckMiddleware(get_response)
        factory = RequestFactory()

        # Test with Azure internal IP but different path
        request = factory.get("/api/games/", HTTP_HOST="169.254.1.1")
        response = middleware(request)
        assert response == "response"
        assert request.META["HTTP_HOST"] == "169.254.1.1"

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_middleware_handles_different_azure_ip_ranges(self):
        """Test that the middleware handles different Azure IP ranges."""

        def get_response(request):
            return "response"

        middleware = AzureHealthCheckMiddleware(get_response)
        factory = RequestFactory()

        # Test various Azure internal IP ranges
        azure_ips = [
            "169.254.0.1",
            "169.254.255.255",
            "169.254.100.50",
        ]

        for ip in azure_ips:
            request = factory.get("/health/", HTTP_HOST=ip)
            response = middleware(request)
            assert response == "response"
            assert request.META["HTTP_HOST"] == "allowed-health-check"

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_middleware_handles_non_azure_ips_correctly(self):
        """Test that the middleware doesn't modify non-Azure IPs."""

        def get_response(request):
            return "response"

        middleware = AzureHealthCheckMiddleware(get_response)
        factory = RequestFactory()

        # Test various non-Azure IPs
        non_azure_ips = [
            "127.0.0.1",
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "169.255.1.1",  # Just outside Azure range
        ]

        for ip in non_azure_ips:
            request = factory.get("/health/", HTTP_HOST=ip)
            response = middleware(request)
            assert response == "response"
            assert request.META["HTTP_HOST"] == ip

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_middleware_integration_with_health_check_view(self):
        """Test that the middleware works correctly with the actual health check view."""

        def get_response(request):
            return health_check(request)

        middleware = AzureHealthCheckMiddleware(get_response)
        factory = RequestFactory()

        # Test Azure IP accessing health check
        request = factory.get("/health/", HTTP_HOST="169.254.1.1")
        response = middleware(request)
        assert response.status_code == 200
        assert response.content == b"ok"
        assert request.META["HTTP_HOST"] == "allowed-health-check"
