import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVariant, STORAGE_KEY } from "../useVariant";
import type { VariantDefinition } from "@/types/variant";

const createMockVariant = (name: string = "test"): VariantDefinition => ({
  name,
  description: "",
  author: "",
  version: "1.0.0",
  soloVictorySCCount: 0,
  nations: [],
  provinces: [
    {
      id: "prov1",
      elementId: "prov1",
      name: "Province 1",
      type: "land",
      path: "M0,0 L10,10",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 5, y: 5 },
      dislodgedUnitPosition: { x: 10, y: 10 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
});

describe("useVariant", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("initialization", () => {
    it("returns null when no saved draft exists", () => {
      const { result } = renderHook(() => useVariant());

      expect(result.current.variant).toBeNull();
    });

    it("loads variant from localStorage on init", () => {
      const mockVariant = createMockVariant("saved");
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariant));

      const { result } = renderHook(() => useVariant());

      expect(result.current.variant).toEqual(mockVariant);
    });

    it("returns null and clears storage when saved data is corrupted", () => {
      localStorage.setItem(STORAGE_KEY, "not valid json{{{");

      const { result } = renderHook(() => useVariant());

      expect(result.current.variant).toBeNull();
      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
  });

  describe("setVariant", () => {
    it("updates variant state", () => {
      const { result } = renderHook(() => useVariant());
      const mockVariant = createMockVariant();

      act(() => {
        result.current.setVariant(mockVariant);
      });

      expect(result.current.variant).toEqual(mockVariant);
    });

    it("saves to localStorage on state change", () => {
      const { result } = renderHook(() => useVariant());
      const mockVariant = createMockVariant();

      act(() => {
        result.current.setVariant(mockVariant);
      });

      const saved = localStorage.getItem(STORAGE_KEY);
      expect(saved).not.toBeNull();
      expect(JSON.parse(saved!)).toEqual(mockVariant);
    });

    it("persists updates across multiple changes", () => {
      const { result } = renderHook(() => useVariant());

      act(() => {
        result.current.setVariant(createMockVariant("first"));
      });

      act(() => {
        result.current.setVariant(createMockVariant("second"));
      });

      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
      expect(saved.name).toBe("second");
    });
  });

  describe("clearDraft", () => {
    it("removes variant from state", () => {
      const { result } = renderHook(() => useVariant());

      act(() => {
        result.current.setVariant(createMockVariant());
      });
      expect(result.current.variant).not.toBeNull();

      act(() => {
        result.current.clearDraft();
      });

      expect(result.current.variant).toBeNull();
    });

    it("removes from localStorage", () => {
      const { result } = renderHook(() => useVariant());

      act(() => {
        result.current.setVariant(createMockVariant());
      });
      expect(localStorage.getItem(STORAGE_KEY)).not.toBeNull();

      act(() => {
        result.current.clearDraft();
      });

      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
  });

  describe("edge cases", () => {
    it("handles localStorage quota exceeded gracefully", () => {
      const { result } = renderHook(() => useVariant());

      const originalSetItem = localStorage.setItem.bind(localStorage);
      localStorage.setItem = vi.fn(() => {
        throw new Error("QuotaExceededError");
      });

      expect(() => {
        act(() => {
          result.current.setVariant(createMockVariant());
        });
      }).not.toThrow();

      expect(result.current.variant).not.toBeNull();

      localStorage.setItem = originalSetItem;
    });
  });
});
