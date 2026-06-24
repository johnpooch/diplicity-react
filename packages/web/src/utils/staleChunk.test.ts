import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { isStaleChunkError, reloadForStaleChunk } from "./staleChunk";

describe("isStaleChunkError", () => {
  it("returns true for a failed dynamic import error", () => {
    const error = new Error(
      "Failed to fetch dynamically imported module: https://www.diplicity.com/assets/OrdersScreen-D67pRsLI.js"
    );
    expect(isStaleChunkError(error)).toBe(true);
  });

  it("returns true for a MIME type module error", () => {
    const error = new Error(
      'Expected a JavaScript-or-Wasm module script but the server responded with a MIME type of "text/html".'
    );
    expect(isStaleChunkError(error)).toBe(true);
  });

  it("returns true for a string error message", () => {
    expect(
      isStaleChunkError("error loading dynamically imported module")
    ).toBe(true);
  });

  it("returns false for an unrelated error", () => {
    expect(isStaleChunkError(new Error("Network request failed"))).toBe(false);
  });

  it("returns false for a non-error value", () => {
    expect(isStaleChunkError(null)).toBe(false);
  });
});

describe("reloadForStaleChunk", () => {
  const reloadMock = vi.fn();

  beforeEach(() => {
    sessionStorage.clear();
    reloadMock.mockClear();
    Object.defineProperty(window, "location", {
      value: { reload: reloadMock },
      writable: true,
    });
    vi.spyOn(Date, "now").mockReturnValue(1_000_000);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reloads the page on the first call", () => {
    reloadForStaleChunk();
    expect(reloadMock).toHaveBeenCalledTimes(1);
  });

  it("does not reload again within the debounce window", () => {
    reloadForStaleChunk();
    reloadForStaleChunk();
    expect(reloadMock).toHaveBeenCalledTimes(1);
  });

  it("reloads again after the debounce window elapses", () => {
    reloadForStaleChunk();
    vi.spyOn(Date, "now").mockReturnValue(1_000_000 + 11_000);
    reloadForStaleChunk();
    expect(reloadMock).toHaveBeenCalledTimes(2);
  });
});
