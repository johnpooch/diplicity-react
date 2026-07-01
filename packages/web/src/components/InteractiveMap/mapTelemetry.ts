import { trace, type Attributes } from "@opentelemetry/api";

const tracer = trace.getTracer("map-performance");

const FRAME_BUDGET_MS = 1000 / 60;
const DROPPED_THRESHOLD = 1.5;

export type GestureType = "pan" | "pinch" | "zoom";

export type MapImplementation = "svg" | "leaflet";

type FrameStats = {
  medianFrameMs: number;
  p95FrameMs: number;
  droppedFramePct: number;
  frameCount: number;
  effectiveFps: number;
};

const median = (xs: number[]): number => {
  if (xs.length === 0) return 0;
  const sorted = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

const percentile = (xs: number[], p: number): number => {
  if (xs.length === 0) return 0;
  const sorted = [...xs].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[idx];
};

const frameStats = (frameMs: number[]): FrameStats => {
  const dropped = frameMs.filter((d) => d > DROPPED_THRESHOLD * FRAME_BUDGET_MS).length;
  const total = frameMs.reduce((a, b) => a + b, 0);
  return {
    medianFrameMs: median(frameMs),
    p95FrameMs: percentile(frameMs, 95),
    droppedFramePct: frameMs.length ? (dropped / frameMs.length) * 100 : 0,
    frameCount: frameMs.length,
    effectiveFps: total > 0 ? (frameMs.length / total) * 1000 : 0,
  };
};

const deviceContext = (): Attributes => {
  const nav = navigator as Navigator & { deviceMemory?: number };
  const attributes: Attributes = {
    "viewport.width": window.innerWidth,
    "viewport.height": window.innerHeight,
    "device.pixel_ratio": window.devicePixelRatio,
    "device.cpu_cores": nav.hardwareConcurrency,
  };
  if (nav.deviceMemory !== undefined) {
    attributes["device.memory_gb"] = nav.deviceMemory;
  }
  return attributes;
};

const recordInitialRender = (params: {
  variantId: string;
  renderMs: number;
  implementation?: MapImplementation;
}): void => {
  const span = tracer.startSpan("map.initial_render", {
    attributes: {
      "map.variant_id": params.variantId,
      "map.render_ms": params.renderMs,
      "map.implementation": params.implementation ?? "svg",
      ...deviceContext(),
    },
  });
  span.end();
};

const recordGesture = (params: {
  variantId: string;
  gestureType: GestureType;
  durationMs: number;
  frameMs: number[];
  implementation?: MapImplementation;
}): void => {
  if (params.frameMs.length === 0) return;
  const stats = frameStats(params.frameMs);
  const span = tracer.startSpan("map.gesture", {
    attributes: {
      "map.variant_id": params.variantId,
      "map.gesture_type": params.gestureType,
      "map.implementation": params.implementation ?? "svg",
      "map.duration_ms": params.durationMs,
      "map.median_frame_ms": stats.medianFrameMs,
      "map.p95_frame_ms": stats.p95FrameMs,
      "map.dropped_frame_pct": stats.droppedFramePct,
      "map.frame_count": stats.frameCount,
      "map.effective_fps": stats.effectiveFps,
      ...deviceContext(),
    },
  });
  span.end();
};

export { recordInitialRender, recordGesture };
