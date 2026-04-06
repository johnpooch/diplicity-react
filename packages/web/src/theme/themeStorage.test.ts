import { beforeEach, describe, expect, it, vi } from "vitest";

// We need to dynamically import themeStorage to reset module state between tests
// since the module uses module-level variables.

const STORAGE_KEY = "theme-preference";

// Default matchMedia mock (light preference, no-op listeners)
const createMatchMediaMock = (prefersDark = false) =>
  vi.fn().mockImplementation(
    (query: string) =>
      ({
        matches:
          query === "(prefers-color-scheme: dark)" ? prefersDark : false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }) as unknown as MediaQueryList
  );

// Helper to reset the DOM and localStorage before each test
const setupDom = () => {
  document.documentElement.classList.remove("dark");
  // Remove any existing theme-color meta
  const existing = document.querySelector('meta[name="theme-color"]');
  if (existing) existing.remove();
  // Add a fresh one
  const meta = document.createElement("meta");
  meta.setAttribute("name", "theme-color");
  meta.setAttribute("content", "#ffffff");
  document.head.appendChild(meta);
};

describe("themeStorage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    setupDom();
    // Set up a default matchMedia mock (jsdom doesn't implement it)
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: createMatchMediaMock(false),
    });
  });

  describe("initialize()", () => {
    it("defaults to 'system' preference when localStorage is empty", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      expect(themeStorage.getThemeState().preference).toBe("system");
    });

    it("reads stored preference from localStorage", async () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      expect(themeStorage.getThemeState().preference).toBe("dark");
    });

    it("applies .dark class when preference is 'dark'", async () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });

    it("does not apply .dark class when preference is 'light'", async () => {
      localStorage.setItem(STORAGE_KEY, "light");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      expect(document.documentElement.classList.contains("dark")).toBe(false);
    });

    it("sets theme-color meta to #1a1a1a for dark theme", async () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const meta = document.querySelector('meta[name="theme-color"]');
      expect(meta?.getAttribute("content")).toBe("#1a1a1a");
    });

    it("sets theme-color meta to #ffffff for light theme", async () => {
      localStorage.setItem(STORAGE_KEY, "light");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const meta = document.querySelector('meta[name="theme-color"]');
      expect(meta?.getAttribute("content")).toBe("#ffffff");
    });

    it("resolves 'system' preference to 'dark' when OS prefers dark", async () => {
      window.matchMedia = createMatchMediaMock(true);
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      expect(themeStorage.getThemeState().resolvedTheme).toBe("dark");
    });

    it("resolves 'system' preference to 'light' when OS prefers light", async () => {
      window.matchMedia = createMatchMediaMock(false);
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      expect(themeStorage.getThemeState().resolvedTheme).toBe("light");
    });

    it("creates theme-color meta if it does not exist", async () => {
      // Remove the meta tag entirely
      const existing = document.querySelector('meta[name="theme-color"]');
      if (existing) existing.remove();

      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const meta = document.querySelector('meta[name="theme-color"]');
      expect(meta).not.toBeNull();
    });
  });

  describe("setPreference()", () => {
    it("updates the cached state", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("dark");
      expect(themeStorage.getThemeState().preference).toBe("dark");
    });

    it("persists preference to localStorage", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("dark");
      expect(localStorage.getItem(STORAGE_KEY)).toBe("dark");
    });

    it("applies .dark class when setting dark preference", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("dark");
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });

    it("removes .dark class when setting light preference", async () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("light");
      expect(document.documentElement.classList.contains("dark")).toBe(false);
    });

    it("notifies listeners when preference changes", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const listener = vi.fn();
      themeStorage.subscribe(listener);
      themeStorage.setPreference("dark");
      expect(listener).toHaveBeenCalledTimes(1);
    });

    it("updates resolvedTheme to 'dark' when setting dark", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("dark");
      expect(themeStorage.getThemeState().resolvedTheme).toBe("dark");
    });

    it("updates resolvedTheme to 'light' when setting light", async () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("light");
      expect(themeStorage.getThemeState().resolvedTheme).toBe("light");
    });
  });

  describe("subscribe()", () => {
    it("returns an unsubscribe function", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const listener = vi.fn();
      const unsubscribe = themeStorage.subscribe(listener);
      unsubscribe();
      themeStorage.setPreference("dark");
      expect(listener).not.toHaveBeenCalled();
    });

    it("multiple listeners are all notified", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const listener1 = vi.fn();
      const listener2 = vi.fn();
      themeStorage.subscribe(listener1);
      themeStorage.subscribe(listener2);
      themeStorage.setPreference("dark");
      expect(listener1).toHaveBeenCalledTimes(1);
      expect(listener2).toHaveBeenCalledTimes(1);
    });
  });

  describe("cross-tab sync via storage event", () => {
    it("updates state and notifies listeners when storage event fires", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const listener = vi.fn();
      themeStorage.subscribe(listener);

      // Simulate another tab changing the preference
      localStorage.setItem(STORAGE_KEY, "dark");
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: STORAGE_KEY,
          newValue: "dark",
          storageArea: localStorage,
        })
      );

      expect(themeStorage.getThemeState().preference).toBe("dark");
      expect(listener).toHaveBeenCalledTimes(1);
    });

    it("ignores storage events for unrelated keys", async () => {
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      const listener = vi.fn();
      themeStorage.subscribe(listener);

      window.dispatchEvent(
        new StorageEvent("storage", {
          key: "some-other-key",
          newValue: "whatever",
          storageArea: localStorage,
        })
      );

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe("system preference reactivity", () => {
    it("attaches matchMedia listener when preference is 'system'", async () => {
      const addEventListener = vi.fn();
      window.matchMedia = vi.fn().mockImplementation(
        (query: string) =>
          ({
            matches: false,
            media: query,
            addEventListener,
            removeEventListener: vi.fn(),
          }) as unknown as MediaQueryList
      );
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      // preference defaults to 'system', so listener should be attached
      expect(addEventListener).toHaveBeenCalledWith(
        "change",
        expect.any(Function)
      );
    });

    it("removes matchMedia listener when switching away from 'system'", async () => {
      const removeEventListener = vi.fn();
      window.matchMedia = vi.fn().mockImplementation(
        (query: string) =>
          ({
            matches: false,
            media: query,
            addEventListener: vi.fn(),
            removeEventListener,
          }) as unknown as MediaQueryList
      );
      const { themeStorage } = await import("./themeStorage");
      themeStorage.initialize();
      themeStorage.setPreference("dark");
      expect(removeEventListener).toHaveBeenCalledWith(
        "change",
        expect.any(Function)
      );
    });
  });
});
