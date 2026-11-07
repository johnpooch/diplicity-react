import asyncio
import datetime
from unittest.mock import AsyncMock, patch

import pytest
import requests
from django.core.management import call_command
from django.urls import reverse
from procrastinate.contrib.django import app
from rest_framework import status

from health.tasks import JOB_RETENTION_HOURS, purge_old_jobs, retry_stalled_jobs


class TestPurgeOldJobs:
    def test_deletes_finished_jobs_beyond_retention_window(self):
        with patch.object(
            app.job_manager, "delete_old_jobs", new_callable=AsyncMock
        ) as mock_delete:
            asyncio.run(purge_old_jobs(timestamp=0))
        mock_delete.assert_awaited_once_with(
            nb_hours=JOB_RETENTION_HOURS,
            include_cancelled=True,
        )


class TestRetryStalledJobs:
    def _doing_job(self, connector, worker_id):
        job = asyncio.run(
            app.configure_task("health.purge_old_jobs").defer_async(timestamp=0)
        )
        asyncio.run(connector.fetch_job_one(queues=None, worker_id=worker_id))
        return job

    def test_retries_job_held_by_dead_worker(self, in_memory_procrastinate):
        worker_id = asyncio.run(in_memory_procrastinate.register_worker_one())[
            "worker_id"
        ]
        in_memory_procrastinate.workers[worker_id] -= datetime.timedelta(hours=1)
        job_id = self._doing_job(in_memory_procrastinate, worker_id)
        asyncio.run(retry_stalled_jobs(timestamp=0))
        assert in_memory_procrastinate.jobs[job_id]["status"] == "todo"

    def test_does_not_retry_job_held_by_live_worker(self, in_memory_procrastinate):
        worker_id = asyncio.run(in_memory_procrastinate.register_worker_one())[
            "worker_id"
        ]
        job_id = self._doing_job(in_memory_procrastinate, worker_id)
        asyncio.run(retry_stalled_jobs(timestamp=0))
        assert in_memory_procrastinate.jobs[job_id]["status"] == "doing"


class TestHealthCheckView:
    """Test the health check endpoint functionality."""

    @pytest.mark.django_db
    def test_health_check_answers_railway_healthcheck_host(
        self, unauthenticated_client
    ):
        response = unauthenticated_client.get(
            reverse("health-check"), HTTP_HOST="healthcheck.railway.app"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b"ok"

    @pytest.mark.django_db
    def test_health_check_rejects_unknown_host(self, unauthenticated_client):
        response = unauthenticated_client.get(
            reverse("health-check"), HTTP_HOST="attacker.example.com"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

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


class TestMarkDeploy:
    @pytest.fixture
    def production_env(self, monkeypatch):
        monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abc123")
        monkeypatch.setenv("HONEYCOMB_MARKERS_API_KEY", "key")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "production")

    def test_posts_one_marker_for_the_release(self, production_env):
        with patch("health.management.commands.mark_deploy.requests.post") as post:
            call_command("mark_deploy")
        post.assert_called_once()
        assert post.call_args.kwargs["json"] == {
            "type": "backend-deploy",
            "message": "Backend deploy abc123",
        }
        assert post.call_args.kwargs["headers"] == {"X-Honeycomb-Team": "key"}

    def test_skips_outside_production(self, production_env, monkeypatch):
        monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "staging")
        with patch("health.management.commands.mark_deploy.requests.post") as post:
            call_command("mark_deploy")
        post.assert_not_called()

    def test_skips_without_api_key(self, production_env, monkeypatch):
        monkeypatch.delenv("HONEYCOMB_MARKERS_API_KEY")
        with patch("health.management.commands.mark_deploy.requests.post") as post:
            call_command("mark_deploy")
        post.assert_not_called()

    def test_swallows_request_failures(self, production_env):
        with patch(
            "health.management.commands.mark_deploy.requests.post",
            side_effect=requests.ConnectionError,
        ):
            call_command("mark_deploy")
