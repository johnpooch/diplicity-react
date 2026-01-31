import { useState, useEffect, useCallback } from "react";
import type { VariantDefinition, Nation, Province, Position, Label } from "@/types/variant";

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

type VariantMetadata = Pick<
  VariantDefinition,
  "name" | "description" | "author" | "soloVictorySCCount"
>;

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

  const updateMetadata = useCallback((updates: Partial<VariantMetadata>) => {
    setVariant((prev) => {
      if (!prev) return null;
      return { ...prev, ...updates };
    });
  }, []);

  const addNation = useCallback((nation: Nation) => {
    setVariant((prev) => {
      if (!prev) return null;
      return { ...prev, nations: [...prev.nations, nation] };
    });
  }, []);

  const updateNation = useCallback(
    (id: string, updates: Partial<Omit<Nation, "id">>) => {
      setVariant((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          nations: prev.nations.map((n) =>
            n.id === id ? { ...n, ...updates } : n
          ),
        };
      });
    },
    []
  );

  const removeNation = useCallback((id: string) => {
    setVariant((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        nations: prev.nations.filter((n) => n.id !== id),
      };
    });
  }, []);

  const setNations = useCallback((nations: Nation[]) => {
    setVariant((prev) => {
      if (!prev) return null;
      return { ...prev, nations };
    });
  }, []);

  const updateProvince = useCallback(
    (id: string, updates: Partial<Omit<Province, "elementId" | "path">>) => {
      setVariant((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          provinces: prev.provinces.map((p) =>
            p.id === id ? { ...p, ...updates } : p
          ),
        };
      });
    },
    []
  );

  const setProvinces = useCallback((provinces: Province[]) => {
    setVariant((prev) => {
      if (!prev) return null;
      return { ...prev, provinces };
    });
  }, []);

  const updateProvincePosition = useCallback(
    (
      provinceId: string,
      positionType: "unitPosition" | "dislodgedUnitPosition" | "supplyCenterPosition",
      position: Position
    ) => {
      setVariant((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          provinces: prev.provinces.map((p) =>
            p.id === provinceId ? { ...p, [positionType]: position } : p
          ),
        };
      });
    },
    []
  );

  const updateProvinceLabel = useCallback(
    (provinceId: string, labelIndex: number, updates: Partial<Label>) => {
      setVariant((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          provinces: prev.provinces.map((p) => {
            if (p.id !== provinceId) return p;
            return {
              ...p,
              labels: p.labels.map((label, idx) =>
                idx === labelIndex ? { ...label, ...updates } : label
              ),
            };
          }),
        };
      });
    },
    []
  );

  return {
    variant,
    setVariant,
    clearDraft,
    updateMetadata,
    addNation,
    updateNation,
    removeNation,
    setNations,
    updateProvince,
    setProvinces,
    updateProvincePosition,
    updateProvinceLabel,
  };
}

export { STORAGE_KEY };
