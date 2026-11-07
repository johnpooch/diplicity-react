import { describe, it, expect, vi } from "vitest";
import { ROOT_CONTEXT, SpanKind } from "@opentelemetry/api";
import { SamplingDecision } from "@opentelemetry/sdk-trace-web";
import {
  TRACE_SAMPLE_RATE,
  currentRouteTemplate,
  deterministicSampler,
  sessionId,
  sessionRouteSpanProcessor,
  setActiveRouter,
} from "./observability";

const sample = (traceId: string) =>
  deterministicSampler.shouldSample(
    ROOT_CONTEXT,
    traceId,
    "HTTP POST",
    SpanKind.CLIENT,
    {},
    []
  );

describe("deterministicSampler", () => {
  it("keeps the same traces as the service sampler, tagged with their sample rate", () => {
    expect(sample("4bf92f3577b34da6a3ce929d0e0e4736")).toEqual({
      decision: SamplingDecision.RECORD_AND_SAMPLED,
      attributes: { SampleRate: TRACE_SAMPLE_RATE },
    });
  });

  it("drops the same traces as the service sampler", () => {
    expect(sample("0af7651916cd43dd8448eb211c80319c").decision).toBe(
      SamplingDecision.NOT_RECORD
    );
  });

  it("always keeps web vital and app launch spans", () => {
    const dropped = "0af7651916cd43dd8448eb211c80319c";
    for (const name of ["web_vital.LCP", "app_launch"]) {
      expect(
        deterministicSampler.shouldSample(
          ROOT_CONTEXT,
          dropped,
          name,
          SpanKind.INTERNAL,
          {},
          []
        )
      ).toEqual({
        decision: SamplingDecision.RECORD_AND_SAMPLED,
        attributes: { SampleRate: 1 },
      });
    }
  });

  it("samples traces at the trace sample rate", () => {
    const traceIds = Array.from({ length: 1000 }, (_, i) =>
      i.toString(16).padStart(32, "0")
    );

    const sampled = traceIds.filter(
      traceId =>
        sample(traceId).decision === SamplingDecision.RECORD_AND_SAMPLED
    );

    expect(sampled).toHaveLength(1000 / TRACE_SAMPLE_RATE);
  });
});

const routerWith = (...paths: (string | undefined)[]) => ({
  state: {
    matches: paths.map(path => ({ route: { path } })),
  },
}) as unknown as Parameters<typeof setActiveRouter>[0];

describe("sessionRouteSpanProcessor", () => {
  it("tags spans with the session id and the matched route template", () => {
    setActiveRouter(
      routerWith("/", "game/:gameId", "phase/:phaseId/orders")
    );
    const span = { setAttribute: vi.fn() };

    sessionRouteSpanProcessor.onStart(span as never, ROOT_CONTEXT);

    expect(span.setAttribute).toHaveBeenCalledWith("session.id", sessionId);
    expect(span.setAttribute).toHaveBeenCalledWith(
      "app.route",
      "/game/:gameId/phase/:phaseId/orders"
    );
  });

  it("resets the template at an absolute child path and skips index routes", () => {
    setActiveRouter(routerWith("/", "ignored", "/forgot-password", undefined));

    expect(currentRouteTemplate()).toBe("/forgot-password");
  });

  it("omits the route when no router is active", () => {
    setActiveRouter(routerWith());

    expect(currentRouteTemplate()).toBeUndefined();
  });
});
