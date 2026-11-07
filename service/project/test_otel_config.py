import time

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

from project.otel_config import (
    TRACE_SAMPLE_RATE,
    DeterministicSampler,
    QueryStatsMiddleware,
    ServerTimingMiddleware,
    client_version_request_hook,
)

SAMPLED_TRACE_ID = 0x4BF92F3577B34DA6A3CE929D0E0E4736
DROPPED_TRACE_ID = 0x0AF7651916CD43DD8448EB211C80319C


def _remote_parent(trace_id):
    span_context = SpanContext(
        trace_id=trace_id,
        span_id=0x00F067AA0BA902B7,
        is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )
    return trace.set_span_in_context(NonRecordingSpan(span_context))


def _export_trace(trace_id):
    exporter = InMemorySpanExporter()
    provider = TracerProvider(sampler=DeterministicSampler())
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer(__name__)
    with tracer.start_as_current_span(
        "GET game/<str:game_id>/", context=_remote_parent(trace_id)
    ):
        with tracer.start_as_current_span("SELECT"):
            pass
    return exporter.get_finished_spans()


class TestDeterministicSampler:
    def test_sampled_trace_keeps_every_span_with_its_sample_rate(self):
        spans = _export_trace(SAMPLED_TRACE_ID)

        assert [span.name for span in spans] == ["SELECT", "GET game/<str:game_id>/"]
        assert all(span.attributes["SampleRate"] == TRACE_SAMPLE_RATE for span in spans)

    def test_unsampled_trace_is_dropped_even_when_the_client_marked_it_sampled(self):
        assert _export_trace(DROPPED_TRACE_ID) == ()

    def test_traces_started_by_the_service_are_sampled_at_the_trace_sample_rate(self):
        sampler = DeterministicSampler()

        sampled = sum(
            sampler.should_sample(None, trace_id, "task").decision.is_sampled()
            for trace_id in range(1000)
        )

        assert sampled == 1000 // TRACE_SAMPLE_RATE


def _client_version_attribute(**headers):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    request = RequestFactory().get("/game/", headers=headers)
    with provider.get_tracer(__name__).start_as_current_span("GET game/") as span:
        client_version_request_hook(span, request)
    return exporter.get_finished_spans()[0].attributes["client.version"]


class TestClientVersionRequestHook:
    def test_request_span_records_the_client_version_header(self):
        assert _client_version_attribute(x_client_version=" 1.4.2 ") == "1.4.2"

    @pytest.mark.parametrize("headers", [{}, {"x_client_version": "   "}])
    def test_request_span_records_none_when_the_client_sends_no_version(self, headers):
        assert _client_version_attribute(**headers) == "none"


def _query_stats_attributes(view):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    middleware = QueryStatsMiddleware(view)
    with provider.get_tracer(__name__).start_as_current_span("GET game/"):
        middleware(RequestFactory().get("/game/"))
    return exporter.get_finished_spans()[0].attributes


@pytest.mark.django_db
class TestQueryStatsMiddleware:
    def test_root_span_records_query_count_and_total_db_time(self):
        def view(request):
            get_user_model().objects.count()
            list(get_user_model().objects.all())
            return HttpResponse()

        attributes = _query_stats_attributes(view)

        assert attributes["db.query_count"] == 2
        assert attributes["db.total_time_ms"] > 0

    def test_root_span_records_zero_queries_for_a_request_without_database_access(self):
        attributes = _query_stats_attributes(lambda request: HttpResponse())

        assert attributes["db.query_count"] == 0
        assert attributes["db.total_time_ms"] == 0

    def test_request_without_a_recording_span_is_passed_through(self):
        response = QueryStatsMiddleware(lambda request: HttpResponse(status=204))(
            RequestFactory().get("/game/")
        )

        assert response.status_code == 204


class TestServerTimingMiddleware:
    def test_response_carries_the_server_duration_and_allows_cross_origin_timing(self):
        response = ServerTimingMiddleware(lambda request: HttpResponse())(
            RequestFactory().get("/game/")
        )

        assert response["Server-Timing"].startswith("app;dur=")
        assert response["Timing-Allow-Origin"] == "*"

    def test_duration_is_in_milliseconds(self):
        def slow_view(request):
            time.sleep(0.05)
            return HttpResponse()

        response = ServerTimingMiddleware(slow_view)(RequestFactory().get("/game/"))

        duration = float(response["Server-Timing"].removeprefix("app;dur="))
        assert 50 <= duration < 1000

    def test_cors_exposes_the_header_to_browsers(self, client):
        response = client.get("/health/", HTTP_ORIGIN="http://localhost:5173")

        assert response["Server-Timing"].startswith("app;dur=")
        assert "server-timing" in response["Access-Control-Expose-Headers"]
