import logging
import os
from datetime import UTC, datetime, timedelta

import requests
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import (
    Gauge,
    Metric,
    MetricExportResult,
    MetricsData,
    NumberDataPoint,
    ResourceMetrics,
    ScopeMetrics,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.util.instrumentation import InstrumentationScope

from health.models import RailwayMetricsCursor

logger = logging.getLogger(__name__)

RAILWAY_API_URL = "https://backboard.railway.com/graphql/v2"
MEASUREMENTS = {
    "CPU_USAGE": ("railway.cpu.usage", "{cpu}"),
    "CPU_LIMIT": ("railway.cpu.limit", "{cpu}"),
    "MEMORY_USAGE_GB": ("railway.memory.usage", "GiBy"),
    "MEMORY_LIMIT_GB": ("railway.memory.limit", "GiBy"),
    "DISK_USAGE_GB": ("railway.disk.usage", "GiBy"),
    "EPHEMERAL_DISK_USAGE_GB": ("railway.ephemeral_disk.usage", "GiBy"),
    "BACKUP_USAGE_GB": ("railway.backup.usage", "GiBy"),
    "NETWORK_RX_GB": ("railway.network.ingress", "GiBy"),
    "NETWORK_TX_GB": ("railway.network.egress", "GiBy"),
}
METRICS_QUERY = """
query RailwayMetrics(
    $environmentId: String!, $startDate: DateTime!, $endDate: DateTime!,
    $measurements: [MetricMeasurement!]!
) {
    environment(id: $environmentId) {
        name
        serviceInstances { edges { node { serviceId serviceName } } }
    }
    resources: metrics(
        environmentId: $environmentId, startDate: $startDate, endDate: $endDate,
        measurements: $measurements, sampleRateSeconds: 60,
        groupBy: [SERVICE_ID, DEPLOYMENT_ID, DEPLOYMENT_INSTANCE_ID, REGION, VOLUME_ID]
    ) {
        measurement
        tags { serviceId deploymentId deploymentInstanceId region volumeId }
        values { ts value }
    }
    network: metrics(
        environmentId: $environmentId, startDate: $startDate, endDate: $endDate,
        measurements: [NETWORK_RX_GB, NETWORK_TX_GB], sampleRateSeconds: 60,
        groupBy: [SERVICE_ID]
    ) {
        measurement
        tags { serviceId }
        values { ts value }
    }
}
"""


class RailwayMetricsError(Exception):
    pass


def export_metrics(timestamp):
    api_token = os.getenv("RAILWAY_METRICS_API_TOKEN")
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID")
    honeycomb_key = os.getenv("HONEYCOMB_API_KEY")
    if not all((api_token, environment_id, honeycomb_key)):
        return 0

    end = datetime.fromtimestamp(timestamp, tz=UTC).replace(second=0, microsecond=0)
    end -= timedelta(minutes=2)
    cursor, _ = RailwayMetricsCursor.objects.get_or_create(
        environment_id=environment_id,
        defaults={"exported_until": end - timedelta(minutes=10)},
    )
    start = cursor.exported_until
    end = min(end, start + timedelta(hours=1))
    if end <= start:
        return 0

    try:
        data = _fetch_metrics(api_token, environment_id, start, end)
        metrics_data = _metrics_data(data, environment_id, start, end)
        if metrics_data.resource_metrics:
            _export_to_honeycomb(metrics_data, honeycomb_key)
    except (requests.RequestException, RailwayMetricsError, ValueError) as error:
        logger.warning("Railway metrics export failed: %s", error)
        return 0

    cursor.exported_until = end
    cursor.save(update_fields=["exported_until"])
    count = sum(
        len(metric.data.data_points)
        for resource in metrics_data.resource_metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
    )
    logger.info("Exported %s Railway metric samples through %s", count, end.isoformat())
    return count


def _fetch_metrics(api_token, environment_id, start, end):
    response = requests.post(
        RAILWAY_API_URL,
        headers={"Authorization": f"Bearer {api_token}"},
        json={
            "query": METRICS_QUERY,
            "variables": {
                "environmentId": environment_id,
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "measurements": [
                    measurement
                    for measurement in MEASUREMENTS
                    if not measurement.startswith("NETWORK_")
                ],
            },
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors") or not payload.get("data"):
        raise RailwayMetricsError("Railway rejected the metrics query")
    return payload["data"]


def _metrics_data(data, environment_id, start, end):
    environment = data["environment"]
    service_names = {
        edge["node"]["serviceId"]: edge["node"]["serviceName"]
        for edge in environment["serviceInstances"]["edges"]
    }
    resource_metrics = {}
    for series in data["resources"] + data["network"]:
        points = [
            NumberDataPoint(
                attributes={},
                start_time_unix_nano=0,
                time_unix_nano=point["ts"] * 1_000_000_000,
                value=point["value"],
            )
            for point in series["values"]
            if start.timestamp() <= point["ts"] < end.timestamp()
        ]
        if not points:
            continue
        tags = series["tags"]
        service_id = tags["serviceId"]
        attributes = {
            "service.name": service_names.get(service_id, service_id),
            "deployment.environment": environment["name"],
            "railway.environment.id": environment_id,
            "railway.service.id": service_id,
        }
        for tag, attribute in (
            ("deploymentId", "railway.deployment.id"),
            ("deploymentInstanceId", "service.instance.id"),
            ("region", "cloud.region"),
            ("volumeId", "railway.volume.id"),
        ):
            if tags.get(tag):
                attributes[attribute] = tags[tag]
        name, unit = MEASUREMENTS[series["measurement"]]
        resource_metrics.setdefault(Resource(attributes), []).append(
            Metric(
                name=name,
                description=series["measurement"],
                unit=unit,
                data=Gauge(data_points=points),
            )
        )
    return MetricsData(
        resource_metrics=[
            ResourceMetrics(
                resource=resource,
                scope_metrics=[
                    ScopeMetrics(
                        scope=InstrumentationScope("health.railway_metrics"),
                        metrics=metrics,
                        schema_url="",
                    )
                ],
                schema_url="",
            )
            for resource, metrics in resource_metrics.items()
        ]
    )


def _export_to_honeycomb(metrics_data, api_key):
    exporter = OTLPMetricExporter(
        endpoint=os.getenv(
            "HONEYCOMB_METRICS_ENDPOINT", "https://api.honeycomb.io:443"
        ),
        headers={"x-honeycomb-team": api_key},
        timeout=10,
    )
    try:
        if (
            exporter.export(metrics_data, timeout_millis=10_000)
            != MetricExportResult.SUCCESS
        ):
            raise RailwayMetricsError("Honeycomb did not accept the metrics export")
    finally:
        exporter.shutdown()
