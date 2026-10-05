from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

from project.otel_config import TRACE_SAMPLE_RATE, DeterministicSampler

SAMPLED_TRACE_ID = 0x4BF92F3577B34DA6A3CE929D0E0E4736
DROPPED_TRACE_ID = 0x0AF7651916CD43DD8448EB211C80319C


def _remote_parent(trace_id):
    span_context = SpanContext(
        trace_id=trace_id, span_id=0x00F067AA0BA902B7, is_remote=True, trace_flags=TraceFlags(TraceFlags.SAMPLED)
    )
    return trace.set_span_in_context(NonRecordingSpan(span_context))


def _export_trace(trace_id):
    exporter = InMemorySpanExporter()
    provider = TracerProvider(sampler=DeterministicSampler())
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer(__name__)
    with tracer.start_as_current_span("GET game/<str:game_id>/", context=_remote_parent(trace_id)):
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

        sampled = sum(sampler.should_sample(None, trace_id, "task").decision.is_sampled() for trace_id in range(1000))

        assert sampled == 1000 // TRACE_SAMPLE_RATE
