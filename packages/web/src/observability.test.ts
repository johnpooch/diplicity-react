import { describe, it, expect, vi, afterEach } from "vitest";
import { ROOT_CONTEXT, SpanKind } from "@opentelemetry/api";
import { SamplingDecision } from "@opentelemetry/sdk-trace-web";
import {
  TRACE_SAMPLE_RATE,
  currentRouteTemplate,
  parseServerDuration,
  deterministicSampler,
  generateSessionId,
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

  it("always keeps page load, web vital, navigation, loading state and chunk spans", () => {
    const dropped = "0af7651916cd43dd8448eb211c80319c";
    for (const name of [
      "web_vital.LCP",
      "app_launch",
      "documentLoad",
      "documentFetch",
      "navigation",
      "game.open",
      "suspense.fallback",
      "chunk.load",
      "chunk.stale_reload",
    ]) {
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

const routerWith = (...paths: (string | undefined)[]) =>
  ({
    state: {
      matches: paths.map(path => ({ route: { path } })),
    },
  }) as unknown as Parameters<typeof setActiveRouter>[0];

describe("sessionRouteSpanProcessor", () => {
  it("tags spans with the session id and the matched route template", () => {
    setActiveRouter(routerWith("/", "game/:gameId", "phase/:phaseId/orders"));
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

describe("parseServerDuration", () => {
  it("reads the app duration in milliseconds", () => {
    expect(parseServerDuration("app;dur=123.4")).toBe(123.4);
  });

  it("finds the app entry among other metrics", () => {
    expect(parseServerDuration("db;dur=5, app;desc=total;dur=42")).toBe(42);
  });

  it("returns undefined when the header is missing or has no app duration", () => {
    expect(parseServerDuration(null)).toBeUndefined();
    expect(parseServerDuration("db;dur=5")).toBeUndefined();
  });
});

describe("generateSessionId", () => {
  const uuidV4 =
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses randomUUID when available", () => {
    vi.stubGlobal("crypto", { randomUUID: () => "fixed-id" });

    expect(generateSessionId()).toBe("fixed-id");
  });

  it("builds a v4 UUID from getRandomValues when randomUUID is missing", () => {
    vi.stubGlobal("crypto", {
      getRandomValues: (bytes: Uint8Array) => bytes.fill(255),
    });

    expect(generateSessionId()).toMatch(uuidV4);
  });

  it("builds a v4 UUID without crypto", () => {
    vi.stubGlobal("crypto", undefined);

    expect(generateSessionId()).toMatch(uuidV4);
  });
});
