import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ComponentType } from "react";

const reloadForStaleChunk = vi.fn();

vi.mock("./staleChunk", () => ({
  reloadForStaleChunk: () => reloadForStaleChunk(),
  isStaleChunkError: (error: unknown) =>
    error instanceof Error && error.message.includes("dynamically imported"),
}));

const recordChunkLoad = vi.fn();
const recordStaleChunkReload = vi.fn();

vi.mock("./chunkTelemetry", () => ({
  recordChunkLoad: (params: unknown) => recordChunkLoad(params),
  recordStaleChunkReload: (source: unknown) => recordStaleChunkReload(source),
}));

import { healLazyImport, resolveScreenModule } from "./lazyScreen";

const Screen: ComponentType = () => null;

describe("resolveScreenModule", () => {
  beforeEach(() => {
    reloadForStaleChunk.mockClear();
    recordChunkLoad.mockClear();
    recordStaleChunkReload.mockClear();
  });

  it("returns the named export when the module loads", async () => {
    const result = await resolveScreenModule(
      () => Promise.resolve({ Screen }),
      "Screen"
    );

    expect(result.default).toBe(Screen);
    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });

  it("reloads when the module resolves to undefined (WebKit/Android stale chunk)", async () => {
    const result = await resolveScreenModule(
      () => Promise.resolve(undefined as unknown as { Screen: ComponentType }),
      "Screen"
    );

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBeTypeOf("function");
  });

  it("reloads when the named export is missing", async () => {
    const result = await resolveScreenModule(
      () =>
        Promise.resolve({} as unknown as { Screen: ComponentType }),
      "Screen"
    );

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBeTypeOf("function");
  });

  it("reloads when the import rejects with a stale-chunk error", async () => {
    const result = await resolveScreenModule(
      () =>
        Promise.reject(
          new Error("Failed to fetch dynamically imported module")
        ) as Promise<{ Screen: ComponentType }>,
      "Screen"
    );

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBeTypeOf("function");
  });

  it("rethrows errors that are not stale-chunk errors", async () => {
    await expect(
      resolveScreenModule(
        () => Promise.reject(new Error("a real bug")) as Promise<{
          Screen: ComponentType;
        }>,
        "Screen"
      )
    ).rejects.toThrow("a real bug");
    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });
});

describe("healLazyImport", () => {
  beforeEach(() => {
    reloadForStaleChunk.mockClear();
    recordChunkLoad.mockClear();
    recordStaleChunkReload.mockClear();
  });

  it("returns the loaded component", async () => {
    const result = await healLazyImport("Screen", () => Promise.resolve(Screen), Screen);

    expect(result.default).toBe(Screen);
    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });

  it("reloads when the load resolves to undefined", async () => {
    const result = await healLazyImport("Screen", () => Promise.resolve(undefined), Screen);

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBe(Screen);
  });

  it("reloads when the load rejects with a stale-chunk error", async () => {
    const result = await healLazyImport(
      "Screen",
      () => Promise.reject(new Error("Failed to fetch dynamically imported module")),
      Screen
    );

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBe(Screen);
  });

  it("rethrows errors that are not stale-chunk errors", async () => {
    await expect(
      healLazyImport("Screen", () => Promise.reject(new Error("a real bug")), Screen)
    ).rejects.toThrow("a real bug");
    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });

  it("records a loaded chunk span with the chunk name", async () => {
    await healLazyImport("Screen", () => Promise.resolve(Screen), Screen);

    expect(recordChunkLoad).toHaveBeenCalledWith(
      expect.objectContaining({ chunk: "Screen", outcome: "loaded" })
    );
    expect(recordStaleChunkReload).not.toHaveBeenCalled();
  });

  it("counts a stale reload when the module is missing", async () => {
    await healLazyImport("Screen", () => Promise.resolve(undefined), Screen);

    expect(recordChunkLoad).toHaveBeenCalledWith(
      expect.objectContaining({ chunk: "Screen", outcome: "stale" })
    );
    expect(recordStaleChunkReload).toHaveBeenCalledWith("missing_module");
  });

  it("counts a stale reload when the import rejects", async () => {
    await healLazyImport(
      "Screen",
      () => Promise.reject(new Error("Failed to fetch dynamically imported module")),
      Screen
    );

    expect(recordStaleChunkReload).toHaveBeenCalledWith("import_error");
  });

  it("records an error span for non-stale failures", async () => {
    await expect(
      healLazyImport("Screen", () => Promise.reject(new Error("a real bug")), Screen)
    ).rejects.toThrow();

    expect(recordChunkLoad).toHaveBeenCalledWith(
      expect.objectContaining({ outcome: "error" })
    );
  });
});
