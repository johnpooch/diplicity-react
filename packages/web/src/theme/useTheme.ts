import { useSyncExternalStore } from "react";
import { themeStorage, type ThemePreference } from "./themeStorage";

const useTheme = () => {
  const { preference, resolvedTheme } = useSyncExternalStore(
    themeStorage.subscribe,
    themeStorage.getThemeState
  );

  return {
    preference,
    resolvedTheme,
    setPreference: (pref: ThemePreference) => themeStorage.setPreference(pref),
  };
};

export { useTheme };
