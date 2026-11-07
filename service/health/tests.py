import asyncio
import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
import requests
from django.core.management import call_command
from django.urls import reverse
from opentelemetry.exporter.otlp.proto.common.metrics_encoder import encode_metrics
from opentelemetry.sdk.metrics.export import Gauge, MetricExportResult
from procrastinate.contrib.django import app
from rest_framework import status

from health.models import RailwayMetricsCursor
from health.railway_metrics import _metrics_data
from health.tasks import (
    JOB_RETENTION_HOURS,
    export_railway_metrics,
    purge_old_jobs,
    retry_stalled_jobs,
)


class TestRailwayMetricsConfiguration:
    @pytest.mark.parametrize(
        "missing",
        ["RAILWAY_METRICS_API_TOKEN", "RAILWAY_ENVIRONMENT_ID", "HONEYCOMB_API_KEY"],
    )
    def test_disabled_without_complete_configuration(self, monkeypatch, missing):
        monkeypatch.setenv("RAILWAY_METRICS_API_TOKEN", "railway-token")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "environment-id")
        monkeypatch.setenv("HONEYCOMB_API_KEY", "honeycomb-key")
        monkeypatch.delenv(missing)
        with patch("health.railway_metrics.requests.post") as post:
            assert export_railway_metrics(timestamp=1800) == 0
        post.assert_not_called()


class TestRailwayMetricsData:
    def test_serialization_preserves_metrics_sharing_a_resource(self):
        data = {
            "environment": {
                "name": "production",
                "serviceInstances": {
                    "edges": [{"node": {"serviceId": "web-id", "serviceName": "web"}}]
                },
            },
            "resources": [
                {
                    "measurement": measurement,
                    "tags": {"serviceId": "web-id"},
                    "values": [
                        {"ts": 1080, "value": 0},
                        {"ts": 1620, "value": 0.25},
                        {"ts": 1680, "value": 99},
                    ],
                }
                for measurement in ("CPU_USAGE", "MEMORY_USAGE_GB")
            ],
            "network": [
                {
                    "measurement": measurement,
                    "tags": {"serviceId": "web-id"},
                    "values": [{"ts": 1620, "value": 0.5}],
                }
                for measurement in ("NETWORK_RX_GB", "NETWORK_TX_GB")
            ],
        }

        encoded = encode_metrics(
            _metrics_data(
                data,
                "environment-id",
                datetime.datetime.fromtimestamp(1080, tz=datetime.UTC),
                datetime.datetime.fromtimestamp(1680, tz=datetime.UTC),
            )
        )

        assert len(encoded.resource_metrics) == 1
        metrics = {
            metric.name: metric
            for scope in encoded.resource_metrics[0].scope_metrics
            for metric in scope.metrics
        }
        assert set(metrics) == {
            "railway.cpu.usage",
            "railway.memory.usage",
            "railway.network.ingress",
            "railway.network.egress",
        }
        assert [
            (point.time_unix_nano, point.as_int, point.as_double)
            for point in metrics["railway.cpu.usage"].gauge.data_points
        ] == [(1_080_000_000_000, 0, 0), (1_620_000_000_000, 0, 0.25)]


@pytest.mark.django_db
class TestRailwayMetricsExport:
    @pytest.fixture
    def configured_export(self, monkeypatch):
        monkeypatch.setenv("RAILWAY_METRICS_API_TOKEN", "railway-token")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "environment-id")
        monkeypatch.setenv("HONEYCOMB_API_KEY", "honeycomb-key")
        monkeypatch.delenv("HONEYCOMB_METRICS_ENDPOINT", raising=False)
        response = Mock()
        response.json.return_value = {
            "data": {
                "environment": {
                    "name": "production",
                    "serviceInstances": {
                        "edges": [
                            {"node": {"serviceId": "web-id", "serviceName": "web"}},
                            {
                                "node": {
                                    "serviceId": "database-id",
                                    "serviceName": "Postgres",
                                }
                            },
                        ]
                    },
                },
                "resources": [
                    {
                        "measurement": measurement,
                        "tags": {
                            "serviceId": "web-id",
                            "deploymentId": "deploy-id",
                            "deploymentInstanceId": "replica-id",
                            "region": "europe-west4",
                        },
                        "values": [{"ts": 1620, "value": value}],
                    }
                    for measurement, value in (
                        ("CPU_USAGE", 0.25),
                        ("CPU_LIMIT", 2),
                        ("MEMORY_USAGE_GB", 0.5),
                        ("MEMORY_LIMIT_GB", 1),
                        ("DISK_USAGE_GB", 3),
                        ("EPHEMERAL_DISK_USAGE_GB", 0.1),
                        ("BACKUP_USAGE_GB", 4),
                    )
                ],
                "network": [
                    {
                        "measurement": measurement,
                        "tags": {"serviceId": "web-id"},
                        "values": [{"ts": 1620, "value": value}],
                    }
                    for measurement, value in (
                        ("NETWORK_RX_GB", 0.125),
                        ("NETWORK_TX_GB", 0.0625),
                    )
                ],
            }
        }
        with (
            patch(
                "health.railway_metrics.requests.post", return_value=response
            ) as post,
            patch("health.railway_metrics.OTLPMetricExporter") as exporter,
        ):
            exporter.return_value.export.return_value = MetricExportResult.SUCCESS
            yield response, post, exporter

    def test_exports_resources_and_service_wide_network_with_original_timestamps(
        self, configured_export
    ):
        response, post, exporter = configured_export
        resources = response.json.return_value["data"]["resources"]
        resources[0]["values"] += [
            {"ts": 1080, "value": 0},
            {"ts": 1079, "value": 99},
            {"ts": 1680, "value": 99},
        ]
        resources[4]["tags"] = {
            "serviceId": "database-id",
            "volumeId": "volume-id",
        }

        assert export_railway_metrics(timestamp=1800) == 10

        assert post.call_args.args == ("https://backboard.railway.com/graphql/v2",)
        assert post.call_args.kwargs["headers"] == {
            "Authorization": "Bearer railway-token"
        }
        assert post.call_args.kwargs["timeout"] == 15
        variables = post.call_args.kwargs["json"]["variables"]
        assert variables["environmentId"] == "environment-id"
        assert variables["startDate"] == "1970-01-01T00:18:00+00:00"
        assert variables["endDate"] == "1970-01-01T00:28:00+00:00"
        assert variables["measurements"] == [
            "CPU_USAGE",
            "CPU_LIMIT",
            "MEMORY_USAGE_GB",
            "MEMORY_LIMIT_GB",
            "DISK_USAGE_GB",
            "EPHEMERAL_DISK_USAGE_GB",
            "BACKUP_USAGE_GB",
        ]
        exporter.assert_called_once_with(
            endpoint="https://api.honeycomb.io:443",
            headers={"x-honeycomb-team": "honeycomb-key"},
            timeout=10,
        )
        metrics_data = exporter.return_value.export.call_args.args[0]
        metrics = {
            metric.name: (resource.resource.attributes, metric)
            for resource in metrics_data.resource_metrics
            for scope in resource.scope_metrics
            for metric in scope.metrics
        }
        assert {
            name: metric.data.data_points[0].value
            for name, (_, metric) in metrics.items()
        } == {
            "railway.cpu.usage": 0.25,
            "railway.cpu.limit": 2,
            "railway.memory.usage": 0.5,
            "railway.memory.limit": 1,
            "railway.disk.usage": 3,
            "railway.ephemeral_disk.usage": 0.1,
            "railway.backup.usage": 4,
            "railway.network.ingress": 0.125,
            "railway.network.egress": 0.0625,
        }
        assert all(isinstance(metric.data, Gauge) for _, metric in metrics.values())
        attributes, cpu = metrics["railway.cpu.usage"]
        assert attributes == {
            "service.name": "web",
            "deployment.environment": "production",
            "railway.environment.id": "environment-id",
            "railway.service.id": "web-id",
            "railway.deployment.id": "deploy-id",
            "service.instance.id": "replica-id",
            "cloud.region": "europe-west4",
        }
        assert cpu.unit == "{cpu}"
        assert [
            (point.time_unix_nano, point.value) for point in cpu.data.data_points
        ] == [
            (1_620_000_000_000, 0.25),
            (1_080_000_000_000, 0),
        ]
        assert metrics["railway.memory.usage"][1].unit == "GiBy"
        assert metrics["railway.disk.usage"][0]["railway.volume.id"] == "volume-id"
        assert metrics["railway.disk.usage"][0]["service.name"] == "Postgres"
        assert "service.instance.id" not in metrics["railway.network.egress"][0]
        exporter.return_value.shutdown.assert_called_once()
        assert (
            RailwayMetricsCursor.objects.get().exported_until.isoformat()
            == variables["endDate"]
        )

    def test_resumes_from_the_last_success_and_ignores_repeated_periods(
        self, configured_export
    ):
        response, post, exporter = configured_export
        export_railway_metrics(timestamp=1800)
        post.reset_mock()
        exporter.reset_mock()

        assert export_railway_metrics(timestamp=1800) == 0
        post.assert_not_called()

        response.json.return_value["data"]["network"][0]["values"] = [
            {"ts": 1680, "value": 0.25}
        ]
        assert export_railway_metrics(timestamp=1860) == 1
        variables = post.call_args.kwargs["json"]["variables"]
        assert variables["startDate"] == "1970-01-01T00:28:00+00:00"
        assert variables["endDate"] == "1970-01-01T00:29:00+00:00"

    @pytest.mark.parametrize(
        "failure", ["timeout", "http", "graphql", "json", "honeycomb"]
    )
    def test_failed_delivery_keeps_the_checkpoint_for_the_next_run(
        self, configured_export, failure, caplog
    ):
        response, post, exporter = configured_export
        if failure == "timeout":
            post.side_effect = requests.Timeout("Railway timed out")
        elif failure == "http":
            response.raise_for_status.side_effect = requests.HTTPError("429")
        elif failure == "graphql":
            response.json.return_value["errors"] = [{"message": "Forbidden"}]
        elif failure == "json":
            response.json.side_effect = ValueError("Invalid JSON")
        else:
            exporter.return_value.export.return_value = MetricExportResult.FAILURE

        assert export_railway_metrics(timestamp=1800) == 0

        assert (
            RailwayMetricsCursor.objects.get().exported_until.isoformat()
            == "1970-01-01T00:18:00+00:00"
        )
        assert "Railway metrics export failed" in caplog.text
        assert all(record.levelname != "ERROR" for record in caplog.records)
        if failure == "honeycomb":
            exporter.return_value.shutdown.assert_called_once()
        else:
            exporter.assert_not_called()

    def test_empty_intervals_advance_without_sending_an_empty_export(
        self, configured_export
    ):
        response, post, exporter = configured_export
        response.json.return_value["data"]["resources"] = []
        response.json.return_value["data"]["network"] = []

        assert export_railway_metrics(timestamp=1800) == 0

        exporter.assert_not_called()
        assert (
            RailwayMetricsCursor.objects.get().exported_until.isoformat()
            == "1970-01-01T00:28:00+00:00"
        )

    def test_backfills_one_hour_at_a_time(self, configured_export):
        response, post, exporter = configured_export
        RailwayMetricsCursor.objects.create(
            environment_id="environment-id",
            exported_until=datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC),
        )

        export_railway_metrics(timestamp=7200)

        variables = post.call_args.kwargs["json"]["variables"]
        assert variables["startDate"] == "1970-01-01T00:00:00+00:00"
        assert variables["endDate"] == "1970-01-01T01:00:00+00:00"

    def test_can_export_to_honeycombs_eu_endpoint(self, configured_export, monkeypatch):
        response, post, exporter = configured_export
        monkeypatch.setenv(
            "HONEYCOMB_METRICS_ENDPOINT", "https://api.eu1.honeycomb.io:443"
        )

        export_railway_metrics(timestamp=1800)

        assert (
            exporter.call_args.kwargs["endpoint"] == "https://api.eu1.honeycomb.io:443"
        )


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
