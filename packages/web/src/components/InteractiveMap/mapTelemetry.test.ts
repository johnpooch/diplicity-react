import { describe, it, expect, vi, beforeEach } from "vitest";

type StartSpan = (
  name: string,
  options: { attributes: Record<string, string | number> }
) => { end: () => void };

const { startSpanSpy, endSpy } = vi.hoisted(() => {
  const endSpy = vi.fn();
  const startSpanSpy = vi.fn<StartSpan>(() => ({ end: endSpy }));
  return { startSpanSpy, endSpy };
});

vi.mock("@opentelemetry/api", () => ({
  trace: { getTracer: () => ({ startSpan: startSpanSpy }) },
}));

import { recordInitialRender, recordGesture, recordRasterFailure } from "./mapTelemetry";

describe("mapTelemetry", () => {
  beforeEach(() => {
    startSpanSpy.mockClear();
    endSpy.mockClear();
  });

  it("emits a map.initial_render span with render time and variant", () => {
    recordInitialRender({ variantId: "classical", renderMs: 12.5 });

    expect(startSpanSpy).toHaveBeenCalledWith(
      "map.initial_render",
      expect.objectContaining({
        attributes: expect.objectContaining({
          "map.variant_id": "classical",
          "map.render_ms": 12.5,
        }),
      })
    );
    expect(endSpy).toHaveBeenCalledTimes(1);
  });

  it("emits a map.gesture span with computed frame statistics", () => {
    recordGesture({
      variantId: "classical",
      gestureType: "pan",
      durationMs: 100,
      frameMs: [16, 16, 40, 16],
    });

    expect(startSpanSpy).toHaveBeenCalledWith(
      "map.gesture",
      expect.objectContaining({
        attributes: expect.objectContaining({
          "map.gesture_type": "pan",
          "map.duration_ms": 100,
          "map.median_frame_ms": 16,
          "map.p95_frame_ms": 40,
          "map.dropped_frame_pct": 25,
          "map.frame_count": 4,
        }),
      })
    );
    expect(endSpy).toHaveBeenCalledTimes(1);
  });

  it("defaults the implementation attribute to svg and honours an explicit value", () => {
    recordInitialRender({ variantId: "classical", renderMs: 1 });
    expect(startSpanSpy).toHaveBeenLastCalledWith(
      "map.initial_render",
      expect.objectContaining({
        attributes: expect.objectContaining({ "map.implementation": "svg" }),
      })
    );

    recordGesture({
      variantId: "classical",
      gestureType: "zoom",
      durationMs: 50,
      frameMs: [16, 16],
      implementation: "leaflet",
    });
    expect(startSpanSpy).toHaveBeenLastCalledWith(
      "map.gesture",
      expect.objectContaining({
        attributes: expect.objectContaining({ "map.implementation": "leaflet" }),
      })
    );
  });

  it("emits a map.raster_failure span with the error message", () => {
    recordRasterFailure({
      variantId: "cold-war-1961",
      error: new Error("Failed to rasterise base map to PNG"),
      implementation: "leaflet",
    });

    expect(startSpanSpy).toHaveBeenCalledWith(
      "map.raster_failure",
      expect.objectContaining({
        attributes: expect.objectContaining({
          "map.variant_id": "cold-war-1961",
          "map.implementation": "leaflet",
          "map.error_message": "Failed to rasterise base map to PNG",
        }),
      })
    );
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
