import { useState, useEffect } from "react";
import { Capacitor } from "@capacitor/core";

export function useIsDesktopWeb(): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (Capacitor.isNativePlatform()) return false;
    return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  });

  useEffect(() => {
    if (Capacitor.isNativePlatform()) return;
    const mql = window.matchMedia("(hover: hover) and (pointer: fine)");
    const onChange = () => setMatches(mql.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return matches;
}
