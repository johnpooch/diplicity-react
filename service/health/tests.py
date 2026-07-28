import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from django.urls import reverse
from procrastinate.contrib.django import app
from rest_framework import status

from health.tasks import JOB_RETENTION_HOURS, purge_old_jobs


class TestPurgeOldJobs:
    def test_deletes_finished_jobs_beyond_retention_window(self):
        with patch.object(app.job_manager, "delete_old_jobs", new_callable=AsyncMock) as mock_delete:
            asyncio.run(purge_old_jobs(timestamp=0))
        mock_delete.assert_awaited_once_with(
            nb_hours=JOB_RETENTION_HOURS,
            include_cancelled=True,
        )


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
