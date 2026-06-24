import { describe, it, expect, vi, beforeEach } from "vitest";

const { startSpanSpy, endSpy } = vi.hoisted(() => {
  const endSpy = vi.fn();
  return { startSpanSpy: vi.fn(() => ({ end: endSpy })), endSpy };
});

vi.mock("@opentelemetry/api", () => ({
  trace: { getTracer: () => ({ startSpan: startSpanSpy }) },
}));

import { recordInitialRender, recordGesture } from "./mapTelemetry";

describe("mapTelemetry", () => {
  beforeEach(() => {
    startSpanSpy.mockClear();
    endSpy.mockClear();
  });

  it("emits a map.initial_render span with render time and variant", () => {
    recordInitialRender({ variantId: "classical", renderMs: 12.5 });

    expect(startSpanSpy).toHaveBeenCalledTimes(1);
    const [name, options] = startSpanSpy.mock.calls[0];
    expect(name).toBe("map.initial_render");
    expect(options.attributes["map.variant_id"]).toBe("classical");
    expect(options.attributes["map.render_ms"]).toBe(12.5);
    expect(endSpy).toHaveBeenCalledTimes(1);
  });

  it("emits a map.gesture span with computed frame statistics", () => {
    recordGesture({
      variantId: "classical",
      gestureType: "pan",
      durationMs: 100,
      frameMs: [16, 16, 40, 16],
    });

    expect(startSpanSpy).toHaveBeenCalledTimes(1);
    const [name, options] = startSpanSpy.mock.calls[0];
    expect(name).toBe("map.gesture");
    expect(options.attributes["map.gesture_type"]).toBe("pan");
    expect(options.attributes["map.duration_ms"]).toBe(100);
    expect(options.attributes["map.median_frame_ms"]).toBe(16);
    expect(options.attributes["map.p95_frame_ms"]).toBe(40);
    expect(options.attributes["map.dropped_frame_pct"]).toBe(25);
    expect(options.attributes["map.frame_count"]).toBe(4);
    expect(endSpy).toHaveBeenCalledTimes(1);
  });

  it("does not emit a gesture span when no frames were recorded", () => {
    recordGesture({
      variantId: "classical",
      gestureType: "zoom",
      durationMs: 50,
      frameMs: [],
    });

    expect(startSpanSpy).not.toHaveBeenCalled();
  });
});
