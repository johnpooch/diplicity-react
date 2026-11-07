import os
import time

from django.db import connection
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import Decision, Sampler, SamplingResult
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

TRACE_SAMPLE_RATE = 10


class DeterministicSampler(Sampler):
    def should_sample(
        self,
        parent_context,
        trace_id,
        name,
        kind=None,
        attributes=None,
        links=None,
        trace_state=None,
    ):
        parent_trace_state = (
            trace.get_current_span(parent_context).get_span_context().trace_state
        )
        if (trace_id & 0xFFFFFFFFFFFFFFFF) % TRACE_SAMPLE_RATE != 0:
            return SamplingResult(Decision.DROP, None, parent_trace_state)
        return SamplingResult(
            Decision.RECORD_AND_SAMPLE,
            {"SampleRate": TRACE_SAMPLE_RATE},
            parent_trace_state,
        )

    def get_description(self):
        return f"DeterministicSampler{{1/{TRACE_SAMPLE_RATE}}}"


def client_version_request_hook(span, request):
    client_version = request.headers.get("X-Client-Version", "").strip()
    span.set_attribute("client.version", client_version or "none")


class QueryStatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        span = trace.get_current_span()
        if not span.is_recording():
            return self.get_response(request)

        stats = {"count": 0, "seconds": 0.0}

        def timed_execute(execute, sql, params, many, context):
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                stats["count"] += 1
                stats["seconds"] += time.perf_counter() - started

        try:
            with connection.execute_wrapper(timed_execute):
                return self.get_response(request)
        finally:
            span.set_attribute("db.query_count", stats["count"])
            span.set_attribute("db.total_time_ms", round(stats["seconds"] * 1000, 2))


class ServerTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response["Server-Timing"] = "app;dur=%.1f" % duration_ms
        response["Timing-Allow-Origin"] = "*"
        return response


def configure_opentelemetry():
    honeycomb_api_key = os.getenv("HONEYCOMB_API_KEY")

    if not honeycomb_api_key:
        print(
            "[OpenTelemetry] HONEYCOMB_API_KEY not set, skipping OpenTelemetry initialization"
        )
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "diplicity-service")

    environment = _detect_environment()

    resource = Resource(
        attributes={
            SERVICE_NAME: service_name,
            DEPLOYMENT_ENVIRONMENT: environment,
        }
    )

    tracer_provider = TracerProvider(resource=resource, sampler=DeterministicSampler())

    otlp_exporter = OTLPSpanExporter(
        endpoint="https://api.honeycomb.io:443",
        headers={
            "x-honeycomb-team": honeycomb_api_key,
        },
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(tracer_provider)

    DjangoInstrumentor().instrument(request_hook=client_version_request_hook)

    RequestsInstrumentor().instrument()

    print(
        f"[OpenTelemetry] Initialized successfully for service '{service_name}' in '{environment}' environment"
    )


def _detect_environment():
    return os.getenv("ENVIRONMENT") or "development"
