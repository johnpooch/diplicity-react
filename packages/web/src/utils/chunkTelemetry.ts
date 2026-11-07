import { trace } from "@opentelemetry/api";

const tracer = trace.getTracer("chunk-loading");

export type StaleChunkSource =
  | "missing_module"
  | "import_error"
  | "preload_error";

export const recordChunkLoad = (params: {
  chunk: string;
  startedAt: number;
  outcome: "loaded" | "stale" | "error";
  navigationWaiting: boolean;
}): void => {
  const span = tracer.startSpan("chunk.load", {
    startTime: params.startedAt,
    attributes: {
      "chunk.name": params.chunk,
      "chunk.outcome": params.outcome,
      "chunk.navigation_waiting": params.navigationWaiting,
    },
  });
  span.end();
};

export const recordStaleChunkReload = (source: StaleChunkSource): void => {
  const span = tracer.startSpan("chunk.stale_reload", {
    attributes: { "chunk.stale_source": source },
  });
  span.end();
};
