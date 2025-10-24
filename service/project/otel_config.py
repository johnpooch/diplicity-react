import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def configure_opentelemetry():
    honeycomb_api_key = os.getenv("HONEYCOMB_API_KEY")

    if not honeycomb_api_key:
        print("[OpenTelemetry] HONEYCOMB_API_KEY not set, skipping OpenTelemetry initialization")
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "diplicity-service")

    environment = _detect_environment()

    resource = Resource(
        attributes={
            SERVICE_NAME: service_name,
            DEPLOYMENT_ENVIRONMENT: environment,
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint="https://api.honeycomb.io:443",
        headers={
            "x-honeycomb-team": honeycomb_api_key,
        },
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(tracer_provider)

    DjangoInstrumentor().instrument()

    Psycopg2Instrumentor().instrument(enable_commenter=True)

    RequestsInstrumentor().instrument()

    print(f"[OpenTelemetry] Initialized successfully for service '{service_name}' in '{environment}' environment")


def _detect_environment():
    debug_mode = os.getenv("DJANGO_DEBUG", "False") == "True"
    if debug_mode:
        return "development"
    else:
        return "production"
