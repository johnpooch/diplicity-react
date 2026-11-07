import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { Suspense, type ComponentType } from "react";
import { act, render, screen } from "@testing-library/react";

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

import {
  healLazyImport,
  lazyScreen,
  prefetchScreens,
  resolveScreenModule,
} from "./lazyScreen";

const Screen: ComponentType = () => null;
const Loaded: ComponentType = () => <p>Loaded</p>;
const staleError = () =>
  new Error("Failed to fetch dynamically imported module");

const renderScreen = (Component: ComponentType) =>
  act(async () => {
    render(
      <Suspense fallback={null}>
        <Component />
      </Suspense>
    );
  });

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
      expect.objectContaining({
        chunk: "Screen",
        outcome: "loaded",
        navigationWaiting: true,
      })
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

  it("rejects without reloading when nobody is waiting on a stale chunk", async () => {
    const error = staleError();

    await expect(
      healLazyImport("Screen", () => Promise.reject(error), Screen, {
        navigationWaiting: false,
      })
    ).rejects.toBe(error);

    expect(reloadForStaleChunk).not.toHaveBeenCalled();
    expect(recordStaleChunkReload).not.toHaveBeenCalled();
    expect(recordChunkLoad).toHaveBeenCalledWith(
      expect.objectContaining({ outcome: "stale", navigationWaiting: false })
    );
  });

  it("rejects without reloading when nobody is waiting on a missing module", async () => {
    await expect(
      healLazyImport("Screen", () => Promise.resolve(undefined), Screen, {
        navigationWaiting: false,
      })
    ).rejects.toThrow("Screen");

    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });
});

describe("lazyScreen", () => {
  beforeEach(() => {
    reloadForStaleChunk.mockClear();
    recordChunkLoad.mockClear();
    recordStaleChunkReload.mockClear();
  });

  it("records a chunk loaded by a render as navigation waiting", async () => {
    const LazyLoaded = lazyScreen(() => Promise.resolve({ Loaded }), "Loaded");

    await renderScreen(LazyLoaded);

    expect(screen.getByText("Loaded")).toBeInTheDocument();
    expect(recordChunkLoad).toHaveBeenCalledOnce();
    expect(recordChunkLoad).toHaveBeenCalledWith(
      expect.objectContaining({ chunk: "Loaded", navigationWaiting: true })
    );
  });

  it("renders a preloaded screen without loading it again", async () => {
    const factory = vi.fn(() => Promise.resolve({ Loaded }));
    const LazyLoaded = lazyScreen(factory, "Loaded");

    await LazyLoaded.preload();
    await renderScreen(LazyLoaded);

    expect(screen.getByText("Loaded")).toBeInTheDocument();
    expect(factory).toHaveBeenCalledOnce();
    expect(recordChunkLoad).toHaveBeenCalledOnce();
    expect(recordChunkLoad).toHaveBeenCalledWith(
      expect.objectContaining({ chunk: "Loaded", navigationWaiting: false })
    );
  });

  it("does not reload when a preload finds a stale chunk", async () => {
    const LazyLoaded = lazyScreen(
      () => Promise.reject(staleError()) as Promise<{ Loaded: ComponentType }>,
      "Loaded"
    );

    await expect(LazyLoaded.preload()).resolves.toBeUndefined();

    expect(reloadForStaleChunk).not.toHaveBeenCalled();
  });

  it("reloads when a render needs a chunk a preload found stale", async () => {
    const factory = vi.fn(
      () => Promise.reject(staleError()) as Promise<{ Loaded: ComponentType }>
    );
    const LazyLoaded = lazyScreen(factory, "Loaded");

    await LazyLoaded.preload();
    await renderScreen(LazyLoaded);

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(factory).toHaveBeenCalledTimes(2);
  });

  it("reloads when a render joins a preload that finds a stale chunk", async () => {
    const factory = vi.fn(
      () => Promise.reject(staleError()) as Promise<{ Loaded: ComponentType }>
    );
    const LazyLoaded = lazyScreen(factory, "Loaded");

    const preload = LazyLoaded.preload();
    await renderScreen(LazyLoaded);
    await preload;

    expect(reloadForStaleChunk).toHaveBeenCalledOnce();
    expect(factory).toHaveBeenCalledTimes(2);
  });
});

describe("prefetchScreens", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    recordChunkLoad.mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("preloads each screen once the previous one has loaded", async () => {
    let resolveFirst: (module: { Loaded: ComponentType }) => void = () => {};
    const first = vi.fn(
      () =>
        new Promise<{ Loaded: ComponentType }>(resolve => {
          resolveFirst = resolve;
        })
    );
    const second = vi.fn(() => Promise.resolve({ Loaded }));

    const prefetch = prefetchScreens({
      First: lazyScreen(first, "Loaded"),
      Second: lazyScreen(second, "Loaded"),
    });
    await vi.runAllTimersAsync();

    expect(first).toHaveBeenCalledOnce();
    expect(second).not.toHaveBeenCalled();

    resolveFirst({ Loaded });
    await vi.runAllTimersAsync();
    await prefetch;

    expect(second).toHaveBeenCalledOnce();
  });

  it("waits for the browser to be idle before each preload", async () => {
    const requestIdleCallback = vi.fn((callback: () => void) => {
      setTimeout(callback, 0);
      return 0;
    });
    vi.stubGlobal("requestIdleCallback", requestIdleCallback);
    const factory = vi.fn(() => Promise.resolve({ Loaded }));

    const prefetch = prefetchScreens({ Screen: lazyScreen(factory, "Loaded") });

    expect(requestIdleCallback).toHaveBeenCalledOnce();
    expect(factory).not.toHaveBeenCalled();

    await vi.runAllTimersAsync();
    await prefetch;

    expect(factory).toHaveBeenCalledOnce();
  });

  it("skips prefetching when the user asked to save data", async () => {
    vi.stubGlobal("navigator", { ...navigator, connection: { saveData: true } });
    const factory = vi.fn(() => Promise.resolve({ Loaded }));

    await prefetchScreens({ Screen: lazyScreen(factory, "Loaded") });
    await vi.runAllTimersAsync();

    expect(factory).not.toHaveBeenCalled();
  });
});
