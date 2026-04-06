import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { themeStorage } from "./themeStorage";
import { useTheme } from "./useTheme";

const STORAGE_KEY = "theme-preference";

// Default matchMedia mock (jsdom doesn't implement it)
const createMatchMediaMock = (prefersDark = false) =>
  vi.fn().mockImplementation(
    (query: string) =>
      ({
        matches: query === "(prefers-color-scheme: dark)" ? prefersDark : false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }) as unknown as MediaQueryList
  );

describe("useTheme", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    document.documentElement.classList.remove("dark");
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: createMatchMediaMock(false),
    });
    // Re-initialize themeStorage to a clean state
    themeStorage.initialize();
  });

  it("returns the current preference", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.preference).toBe("system");
  });

  it("returns the resolved theme", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.resolvedTheme).toBe("light");
  });

  it("exposes setPreference function", () => {
    const { result } = renderHook(() => useTheme());
    expect(typeof result.current.setPreference).toBe("function");
  });

  it("updates preference reactively when setPreference is called", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.setPreference("dark");
    });
    expect(result.current.preference).toBe("dark");
  });

  it("updates resolvedTheme reactively when setPreference is called", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.setPreference("dark");
    });
    expect(result.current.resolvedTheme).toBe("dark");
  });

  it("reflects changes made via themeStorage.setPreference directly", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      themeStorage.setPreference("dark");
    });
    expect(result.current.preference).toBe("dark");
  });

  it("persists the localStorage key when setPreference is called", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.setPreference("dark");
    });
    expect(localStorage.getItem(STORAGE_KEY)).toBe("dark");
  });
});
