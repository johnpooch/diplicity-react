import { WebTracerProvider, BatchSpanProcessor } from "@opentelemetry/sdk-trace-web";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions/incubating";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { DocumentLoadInstrumentation } from "@opentelemetry/instrumentation-document-load";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";
import { XMLHttpRequestInstrumentation } from "@opentelemetry/instrumentation-xml-http-request";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { ZoneContextManager } from "@opentelemetry/context-zone";

export function initializeObservability() {
  const honeycombApiKey = import.meta.env.VITE_HONEYCOMB_API_KEY;

  if (!honeycombApiKey) {
    console.log(
      "[OpenTelemetry] VITE_HONEYCOMB_API_KEY not set, skipping OpenTelemetry initialization"
    );
    return;
  }

  const serviceName =
    import.meta.env.VITE_OTEL_SERVICE_NAME || "diplicity-web";
  const environment = detectEnvironment();

  const resource = resourceFromAttributes({
    [ATTR_SERVICE_NAME]: serviceName,
    "deployment.environment": environment,
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
    spanProcessors: [spanProcessor],
  });

  provider.register({
    contextManager: new ZoneContextManager(),
  });

  registerInstrumentations({
    instrumentations: [
      new DocumentLoadInstrumentation(),
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: [
          new RegExp(import.meta.env.VITE_DIPLICITY_API_BASE_URL || "http://localhost:8000"),
        ],
        clearTimingResources: true,
      }),
      new XMLHttpRequestInstrumentation({
        propagateTraceHeaderCorsUrls: [
          new RegExp(import.meta.env.VITE_DIPLICITY_API_BASE_URL || "http://localhost:8000"),
        ],
        clearTimingResources: true,
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
