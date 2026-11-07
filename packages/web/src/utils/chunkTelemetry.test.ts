import { describe, it, expect, vi, beforeEach } from "vitest";

type StartSpan = (
  name: string,
  options: { attributes: Record<string, string | number | boolean>; startTime?: number }
) => { end: () => void };

const { startSpanSpy, endSpy } = vi.hoisted(() => {
  const endSpy = vi.fn();
  const startSpanSpy = vi.fn<StartSpan>(() => ({ end: endSpy }));
  return { startSpanSpy, endSpy };
});

vi.mock("@opentelemetry/api", () => ({
  trace: { getTracer: () => ({ startSpan: startSpanSpy }) },
}));

import { recordChunkLoad, recordStaleChunkReload } from "./chunkTelemetry";

describe("chunkTelemetry", () => {
  beforeEach(() => {
    startSpanSpy.mockClear();
    endSpy.mockClear();
  });

  it("emits a chunk.load span from the import start time", () => {
    recordChunkLoad({
      chunk: "MyGames",
      startedAt: 1000,
      outcome: "loaded",
      navigationWaiting: true,
    });

    expect(startSpanSpy).toHaveBeenCalledWith("chunk.load", {
      startTime: 1000,
      attributes: {
        "chunk.name": "MyGames",
        "chunk.outcome": "loaded",
        "chunk.navigation_waiting": true,
      },
    });
    expect(endSpy).toHaveBeenCalledOnce();
  });

  it("records a chunk nobody was waiting on as not navigation waiting", () => {
    recordChunkLoad({
      chunk: "MyGames",
      startedAt: 1000,
      outcome: "loaded",
      navigationWaiting: false,
    });

    expect(startSpanSpy).toHaveBeenCalledWith(
      "chunk.load",
      expect.objectContaining({
        attributes: expect.objectContaining({
          "chunk.navigation_waiting": false,
        }),
      })
    );
  });

  it("emits a chunk.stale_reload span with its source", () => {
    recordStaleChunkReload("preload_error");

    expect(startSpanSpy).toHaveBeenCalledWith("chunk.stale_reload", {
      attributes: { "chunk.stale_source": "preload_error" },
    });
    expect(endSpy).toHaveBeenCalledOnce();
  });
});
