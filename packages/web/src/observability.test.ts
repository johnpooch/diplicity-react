import { describe, it, expect, vi, afterEach } from "vitest";
import { ROOT_CONTEXT, SpanKind } from "@opentelemetry/api";
import { SamplingDecision } from "@opentelemetry/sdk-trace-web";
import {
  TRACE_SAMPLE_RATE,
  currentRouteTemplate,
  isServedFromCache,
  parseServerDuration,
  deterministicSampler,
  generateSessionId,
  sessionId,
  sessionRouteSpanProcessor,
  initializeObservability,
  setActiveRouter,
  setNativeVersions,
  versionSpanProcessor,
} from "./observability";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";

vi.mock("@opentelemetry/instrumentation", async importOriginal => ({
  ...(await importOriginal<typeof import("@opentelemetry/instrumentation")>()),
  registerInstrumentations: vi.fn(),
}));

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

describe("versionSpanProcessor", () => {
  it("adds the bundle and native versions once they are known", () => {
    const before = { setAttribute: vi.fn() };
    versionSpanProcessor.onStart(before as never, ROOT_CONTEXT);
    expect(before.setAttribute).not.toHaveBeenCalled();

    setNativeVersions({ otaBundle: "1.5.12.4", nativeBinary: "1.5.12" });
    const after = { setAttribute: vi.fn() };
    versionSpanProcessor.onStart(after as never, ROOT_CONTEXT);

    expect(after.setAttribute).toHaveBeenCalledWith(
      "app.ota_bundle_version",
      "1.5.12.4"
    );
    expect(after.setAttribute).toHaveBeenCalledWith(
      "app.native_version",
      "1.5.12"
    );
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

describe("initializeObservability", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("does not trace uploads to Honeycomb", () => {
    vi.stubEnv("VITE_HONEYCOMB_API_KEY", "test-key");

    initializeObservability();

    const { instrumentations } = vi.mocked(registerInstrumentations).mock
      .calls[0][0];
    const fetchInstrumentation = instrumentations?.find(
      instrumentation => instrumentation instanceof FetchInstrumentation
    ) as FetchInstrumentation;
    const { ignoreUrls } = fetchInstrumentation.getConfig();
    const ignored = (url: string) =>
      ignoreUrls?.some(pattern => new RegExp(pattern).test(url));

    expect(ignored("https://api.honeycomb.io/v1/traces")).toBe(true);
    expect(ignored("https://api.diplicity.com/games/")).toBe(false);
  });
});

describe("isServedFromCache", () => {
  it("is true when bytes were decoded without any transfer", () => {
    expect(isServedFromCache({ transferSize: 0, decodedBodySize: 512 })).toBe(
      true
    );
  });

  it("is false when bytes crossed the network", () => {
    expect(isServedFromCache({ transferSize: 800, decodedBodySize: 512 })).toBe(
      false
    );
  });

  it("is false for an empty body", () => {
    expect(isServedFromCache({ transferSize: 0, decodedBodySize: 0 })).toBe(
      false
    );
  });
});
