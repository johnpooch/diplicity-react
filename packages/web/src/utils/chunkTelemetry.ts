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
}): void => {
  const span = tracer.startSpan("chunk.load", {
    startTime: params.startedAt,
    attributes: {
      "chunk.name": params.chunk,
      "chunk.outcome": params.outcome,
      "chunk.navigation_waiting": true,
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
