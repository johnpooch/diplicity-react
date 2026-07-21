import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ComponentType } from "react";

const reloadForStaleChunk = vi.fn();

vi.mock("./staleChunk", () => ({
  reloadForStaleChunk: () => reloadForStaleChunk(),
  isStaleChunkError: (error: unknown) =>
    error instanceof Error && error.message.includes("dynamically imported"),
}));

import { healLazyImport, resolveScreenModule } from "./lazyScreen";

const Screen: ComponentType = () => null;

describe("resolveScreenModule", () => {
  beforeEach(() => {
    reloadForStaleChunk.mockClear();
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
  });

  it("returns the loaded component", async () => {
    const result = await healLazyImport(() => Promise.resolve(Screen), Screen);

    expect(result.default).toBe(Screen);
    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });

  it("reloads when the load resolves to undefined", async () => {
    const result = await healLazyImport(() => Promise.resolve(undefined), Screen);

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBe(Screen);
  });

  it("reloads when the load rejects with a stale-chunk error", async () => {
    const result = await healLazyImport(
      () => Promise.reject(new Error("Failed to fetch dynamically imported module")),
      Screen
    );

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(result.default).toBe(Screen);
  });

  it("rethrows errors that are not stale-chunk errors", async () => {
    await expect(
      healLazyImport(() => Promise.reject(new Error("a real bug")), Screen)
    ).rejects.toThrow("a real bug");
    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });
});
