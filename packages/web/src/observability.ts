import {
  WebTracerProvider,
  BatchSpanProcessor,
  SamplingDecision,
  type Sampler,
  type Span,
  type SpanProcessor,
} from "@opentelemetry/sdk-trace-web";
import type { Span as ApiSpan } from "@opentelemetry/api";
import type { DataRouter } from "react-router";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions/incubating";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { DocumentLoadInstrumentation } from "@opentelemetry/instrumentation-document-load";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";
import { XMLHttpRequestInstrumentation } from "@opentelemetry/instrumentation-xml-http-request";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { ZoneContextManager } from "@opentelemetry/context-zone";
import { APP_LAUNCH_SPAN_NAME, WEB_VITAL_SPAN_PREFIX } from "./webVitals";
import { Capacitor } from "@capacitor/core";
import { requestTagFor, trackXhrRequestTags } from "./api/requestTelemetry";

export const TRACE_SAMPLE_RATE = 10;

const FULL_RATE_SPAN_NAMES = new Set([
  APP_LAUNCH_SPAN_NAME,
  "documentLoad",
  "documentFetch",
  "navigation",
  "game.open",
  "suspense.fallback",
  "chunk.load",
  "chunk.stale_reload",
]);

const isFullRateSpan = (spanName: string) =>
  FULL_RATE_SPAN_NAMES.has(spanName) ||
  spanName.startsWith(WEB_VITAL_SPAN_PREFIX);

export const deterministicSampler: Sampler = {
  shouldSample(_context, traceId, spanName) {
    if (isFullRateSpan(spanName)) {
      return {
        decision: SamplingDecision.RECORD_AND_SAMPLED,
        attributes: { SampleRate: 1 },
      };
    }
    if (BigInt(`0x${traceId.slice(16)}`) % BigInt(TRACE_SAMPLE_RATE) !== 0n) {
      return { decision: SamplingDecision.NOT_RECORD };
    }
    return {
      decision: SamplingDecision.RECORD_AND_SAMPLED,
      attributes: { SampleRate: TRACE_SAMPLE_RATE },
    };
  },
  toString: () => `DeterministicSampler{1/${TRACE_SAMPLE_RATE}}`,
};

export const generateSessionId = (): string => {
  if (typeof crypto?.randomUUID === "function") {
    return crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  if (typeof crypto?.getRandomValues === "function") {
    crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i++) {
      bytes[i] = Math.floor(Math.random() * 256);
    }
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, "0"));
  return [
    hex.slice(0, 4).join(""),
    hex.slice(4, 6).join(""),
    hex.slice(6, 8).join(""),
    hex.slice(8, 10).join(""),
    hex.slice(10).join(""),
  ].join("-");
};

export const sessionId = generateSessionId();

let activeRouter: Pick<DataRouter, "state"> | null = null;

export const setActiveRouter = (router: Pick<DataRouter, "state">) => {
  activeRouter = router;
};

export const currentRouteTemplate = (): string | undefined => {
  if (!activeRouter) return undefined;
  let template = "";
  for (const match of activeRouter.state.matches) {
    const path = match.route.path;
    if (path === undefined) continue;
    template = path.startsWith("/") ? path : `${template}/${path}`;
  }
  return template.replace(/\/+/g, "/") || undefined;
};

export const sessionRouteSpanProcessor: SpanProcessor = {
  onStart(span: Span) {
    span.setAttribute("session.id", sessionId);
    const route = currentRouteTemplate();
    if (route) {
      span.setAttribute("app.route", route);
    }
  },
  onEnd() {},
  forceFlush: () => Promise.resolve(),
  shutdown: () => Promise.resolve(),
};

let nativeVersions: { otaBundle: string; nativeBinary: string } | null = null;

export const setNativeVersions = (versions: {
  otaBundle: string;
  nativeBinary: string;
}) => {
  nativeVersions = versions;
};

export const versionSpanProcessor: SpanProcessor = {
  onStart(span: Span) {
    if (!nativeVersions) return;
    span.setAttribute("app.ota_bundle_version", nativeVersions.otaBundle);
    span.setAttribute("app.native_version", nativeVersions.nativeBinary);
  },
  onEnd() {},
  forceFlush: () => Promise.resolve(),
  shutdown: () => Promise.resolve(),
};

export const parseServerDuration = (
  header: string | null | undefined
): number | undefined => {
  const match = header?.match(/(?:^|,)\s*app;(?:[^,]*;)?dur=(\d+(?:\.\d+)?)/);
  return match ? Number(match[1]) : undefined;
};

export const isServedFromCache = (
  entry: Pick<PerformanceResourceTiming, "transferSize" | "decodedBodySize">
): boolean => entry.transferSize === 0 && entry.decodedBodySize > 0;

const lookupServedFromCache = (url: string): boolean => {
  if (!url || typeof performance?.getEntriesByName !== "function") {
    return false;
  }
  const entries = performance.getEntriesByName(url, "resource");
  const entry = entries[entries.length - 1] as
    | PerformanceResourceTiming
    | undefined;
  return entry !== undefined && isServedFromCache(entry);
};

const recordServerDuration = (
  span: Span | ApiSpan,
  header: string | null | undefined,
  url: string
) => {
  if (lookupServedFromCache(url)) {
    span.setAttribute("http.cache_hit", true);
    return;
  }
  span.setAttribute("http.cache_hit", false);
  const duration = parseServerDuration(header);
  if (duration !== undefined) {
    span.setAttribute("http.server_duration_ms", duration);
  }
};

export function initializeObservability() {
  const honeycombApiKey = import.meta.env.VITE_HONEYCOMB_API_KEY;

  if (!honeycombApiKey) {
    console.log(
      "[OpenTelemetry] VITE_HONEYCOMB_API_KEY not set, skipping OpenTelemetry initialization"
    );
    return;
  }

  const serviceName = import.meta.env.VITE_OTEL_SERVICE_NAME || "diplicity-web";
  const environment = detectEnvironment();

  const resource = resourceFromAttributes({
    [ATTR_SERVICE_NAME]: serviceName,
    "deployment.environment": environment,
    "app.platform": Capacitor.getPlatform(),
    "app.version": __APP_VERSION__,
    "app.git_sha": __GIT_SHA__,
  });

  const exporter = new OTLPTraceExporter({
    url: "https://api.honeycomb.io/v1/traces",
    headers: {
      "x-honeycomb-team": honeycombApiKey,
    },
  });

  const spanProcessor = new BatchSpanProcessor(exporter);

  const provider = new WebTracerProvider({
    resource,
    sampler: deterministicSampler,
    spanProcessors: [
      sessionRouteSpanProcessor,
      versionSpanProcessor,
      spanProcessor,
    ],
  });

  trackXhrRequestTags();

  provider.register({
    contextManager: new ZoneContextManager(),
  });

  registerInstrumentations({
    instrumentations: [
      new DocumentLoadInstrumentation(),
      new FetchInstrumentation({
        ignoreUrls: [/api\.honeycomb\.io/],
        propagateTraceHeaderCorsUrls: [
          new RegExp(
            import.meta.env.VITE_DIPLICITY_API_BASE_URL ||
              "http://localhost:8000"
          ),
        ],
        clearTimingResources: true,
        applyCustomAttributesOnSpan: (span, _request, result) => {
          if (result instanceof Response) {
            recordServerDuration(
              span,
              result.headers.get("server-timing"),
              result.url
            );
          }
        },
      }),
      new XMLHttpRequestInstrumentation({
        propagateTraceHeaderCorsUrls: [
          new RegExp(
            import.meta.env.VITE_DIPLICITY_API_BASE_URL ||
              "http://localhost:8000"
          ),
        ],
        clearTimingResources: true,
        applyCustomAttributesOnSpan: (span, xhr) => {
          const tag = requestTagFor(xhr);
          if (tag) {
            span.setAttribute("request.blocking", tag.blocking);
            span.setAttribute("request.reason", tag.reason);
            span.setAttribute("request.duplicate", tag.duplicate);
          }
          recordServerDuration(
            span,
            xhr.getResponseHeader("server-timing"),
            xhr.responseURL
          );
        },
      }),
    ],
  });

  console.log(
    `[OpenTelemetry] Initialized successfully for service '${serviceName}' in '${environment}' environment`
  );
}

function detectEnvironment(): string {
  const mode = import.meta.env.MODE;

  if (mode === "development") {
    return "development";
  } else if (mode === "production") {
    return "production";
  } else {
    return mode || "unknown";
  }
}
