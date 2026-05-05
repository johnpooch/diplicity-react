type ThemePreference = "light" | "dark" | "system";
type ResolvedTheme = "light" | "dark";
type ThemeState = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
};

type ThemeChangeListener = () => void;

const STORAGE_KEY = "theme-preference";

const listeners: Set<ThemeChangeListener> = new Set();

let cachedState: ThemeState = {
  preference: "system",
  resolvedTheme: "light",
};

// Holds the current matchMedia listener so it can be removed when switching away from "system"
let mediaQueryListener: ((e: MediaQueryListEvent) => void) | null = null;
let mediaQuery: MediaQueryList | null = null;

const getSystemResolvedTheme = (): ResolvedTheme => {
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  } catch {
    return "light";
  }
};

const resolveTheme = (preference: ThemePreference): ResolvedTheme => {
  if (preference === "system") {
    return getSystemResolvedTheme();
  }
  return preference;
};

const applyTheme = (resolvedTheme: ResolvedTheme) => {
  if (resolvedTheme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }

  const themeColor = resolvedTheme === "dark" ? "#1a1a1a" : "#ffffff";
  let meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement("meta");
    meta.setAttribute("name", "theme-color");
    document.head.appendChild(meta);
  }
  meta.setAttribute("content", themeColor);
};

const notifyListeners = () => {
  listeners.forEach(listener => listener());
};

const updateCachedState = (preference: ThemePreference) => {
  const resolvedTheme = resolveTheme(preference);
  cachedState = { preference, resolvedTheme };
  applyTheme(resolvedTheme);
};

const detachMediaQueryListener = () => {
  if (mediaQuery && mediaQueryListener) {
    mediaQuery.removeEventListener("change", mediaQueryListener);
    mediaQueryListener = null;
    mediaQuery = null;
  }
};

const attachMediaQueryListener = () => {
  detachMediaQueryListener();
  mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQueryListener = () => {
    updateCachedState("system");
    notifyListeners();
  };
  mediaQuery.addEventListener("change", mediaQueryListener);
};

const handleStorageEvent = (event: StorageEvent) => {
  if (event.key !== STORAGE_KEY || event.storageArea !== localStorage) {
    return;
  }
  const newPreference = (event.newValue as ThemePreference | null) ?? "system";
  if (newPreference === "system") {
    attachMediaQueryListener();
  } else {
    detachMediaQueryListener();
  }
  updateCachedState(newPreference);
  notifyListeners();
};

const initialize = () => {
  let preference: ThemePreference = "system";
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") {
      preference = stored;
    }
  } catch {
    // localStorage unavailable — fall back to "system"
  }

  if (preference === "system") {
    attachMediaQueryListener();
  }

  updateCachedState(preference);
  window.addEventListener("storage", handleStorageEvent);
};

const setPreference = (preference: ThemePreference) => {
  try {
    localStorage.setItem(STORAGE_KEY, preference);
  } catch {
    // localStorage unavailable — still apply in-memory
  }

  if (preference === "system") {
    attachMediaQueryListener();
  } else {
    detachMediaQueryListener();
  }

  updateCachedState(preference);
  notifyListeners();
};

const getThemeState = (): ThemeState => cachedState;

const subscribe = (listener: ThemeChangeListener) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

export const themeStorage = {
  initialize,
  setPreference,
  getThemeState,
  subscribe,
};

export type { ThemePreference, ResolvedTheme, ThemeState };
