import { useState, useEffect, useCallback } from "react";
import type { VariantDefinition } from "@/types/variant";

const STORAGE_KEY = "variant-creator-draft";

function loadFromStorage(): VariantDefinition | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return null;
    return JSON.parse(saved) as VariantDefinition;
  } catch {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function useVariant() {
  const [variant, setVariant] = useState<VariantDefinition | null>(() => {
    return loadFromStorage();
  });

  useEffect(() => {
    if (variant) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(variant));
      } catch {
        // localStorage full - fail silently
      }
    }
  }, [variant]);

  const clearDraft = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setVariant(null);
  }, []);

  return { variant, setVariant, clearDraft };
}

export { STORAGE_KEY };
