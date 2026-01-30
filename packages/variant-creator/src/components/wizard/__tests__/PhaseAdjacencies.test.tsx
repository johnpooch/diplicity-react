import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PhaseAdjacencies } from "../PhaseAdjacencies";
import { STORAGE_KEY } from "@/hooks/useVariant";

vi.mock("@/utils/geometry", () => ({
  calculateCentroid: vi.fn(() => ({ x: 20, y: 20 })),
  calculatePositions: vi.fn(() => ({
    unitPosition: { x: 20, y: 20 },
    dislodgedUnitPosition: { x: 35, y: 35 },
    supplyCenterPosition: { x: 8, y: 8 },
  })),
  detectPathIntersections: vi.fn((pathA: string, pathB: string) => {
    if (pathA.includes("adjacent-to-b") && pathB.includes("province-b")) {
      return true;
    }
    if (pathA.includes("province-b") && pathB.includes("adjacent-to-b")) {
      return true;
    }
    return false;
  }),
}));

const mockVariantWithProvinces = {
  name: "Test Variant",
  description: "",
  author: "",
  version: "1.0.0",
  soloVictorySCCount: 18,
  nations: [{ id: "england", name: "England", color: "#2196F3" }],
  provinces: [
    {
      id: "ber",
      elementId: "province-1",
      name: "Berlin",
      type: "land" as const,
      path: "M10,10 adjacent-to-b L30,10 L30,30 L10,30 Z",
      homeNation: "england",
      supplyCenter: true,
      startingUnit: { type: "Army" as const },
      adjacencies: [],
      labels: [],
      unitPosition: { x: 20, y: 20 },
      dislodgedUnitPosition: { x: 35, y: 35 },
      supplyCenterPosition: { x: 8, y: 8 },
    },
    {
      id: "mun",
      elementId: "province-2",
      name: "Munich",
      type: "land" as const,
      path: "M40,10 province-b L60,10 L60,30 L40,30 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 50, y: 20 },
      dislodgedUnitPosition: { x: 65, y: 35 },
    },
    {
      id: "par",
      elementId: "province-3",
      name: "Paris",
      type: "land" as const,
      path: "M100,100 L120,100 L120,120 L100,120 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 110, y: 110 },
      dislodgedUnitPosition: { x: 125, y: 125 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 200, height: 200 },
  textElements: [],
};

const mockVariantNoProvinces = {
  ...mockVariantWithProvinces,
  provinces: [],
};

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <PhaseAdjacencies />
    </MemoryRouter>
  );
}

describe("PhaseAdjacencies", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("with provinces", () => {
    beforeEach(() => {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(mockVariantWithProvinces)
      );
    });

    it("renders adjacencies section", () => {
      renderWithRouter();
      expect(screen.getByText("Province Adjacencies")).toBeInTheDocument();
    });

    it("displays province navigation", () => {
      renderWithRouter();
      expect(screen.getByText("Previous")).toBeInTheDocument();
      expect(screen.getByText("Next")).toBeInTheDocument();
      expect(screen.getByText(/Province 1 of 3/)).toBeInTheDocument();
    });

    it("shows first province name", () => {
      renderWithRouter();
      expect(screen.getByText("Berlin")).toBeInTheDocument();
    });

    it("navigates to next province when clicking Next", async () => {
      renderWithRouter();

      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Province 2 of 3/)).toBeInTheDocument();
      });
    });

    it("navigates to previous province when clicking Previous", async () => {
      renderWithRouter();

      const prevButton = screen.getByText("Previous");
      fireEvent.click(prevButton);

      await waitFor(() => {
        expect(screen.getByText(/Province 3 of 3/)).toBeInTheDocument();
      });
    });

    it("renders the map with provinces", () => {
      renderWithRouter();

      const svg = document.querySelector("svg");
      expect(svg).toBeInTheDocument();

      const paths = document.querySelectorAll("path");
      expect(paths.length).toBeGreaterThanOrEqual(3);
    });

    it("renders auto-detect button", () => {
      renderWithRouter();
      expect(screen.getByText("Auto-Detect Adjacencies")).toBeInTheDocument();
    });

    it("shows connections count", () => {
      renderWithRouter();
      expect(screen.getByText(/0 connections defined/)).toBeInTheDocument();
    });

    it("shows warning for isolated provinces when all have no adjacencies", () => {
      renderWithRouter();

      expect(
        screen.getByText(/3 provinces with no adjacencies/)
      ).toBeInTheDocument();
    });

    it("shows empty adjacencies message", () => {
      renderWithRouter();

      expect(
        screen.getByText(/No adjacencies defined. Click provinces on the map/)
      ).toBeInTheDocument();
    });

    it("auto-detects adjacencies when clicking Auto-Detect", async () => {
      renderWithRouter();

      const autoDetectButton = screen.getByText("Auto-Detect Adjacencies");
      fireEvent.click(autoDetectButton);

      await waitFor(() => {
        expect(screen.getByText(/1 connections defined/)).toBeInTheDocument();
      });
    });

    it("persists adjacencies to localStorage", async () => {
      renderWithRouter();

      const autoDetectButton = screen.getByText("Auto-Detect Adjacencies");
      fireEvent.click(autoDetectButton);

      await waitFor(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        const parsed = JSON.parse(saved!);
        const berlinProvince = parsed.provinces.find(
          (p: { id: string }) => p.id === "ber"
        );
        expect(berlinProvince.adjacencies).toContain("mun");
      });
    });

    it("shows adjacency table header with province name", () => {
      renderWithRouter();

      expect(screen.getByText(/Adjacent to Berlin/)).toBeInTheDocument();
    });
  });

  describe("without provinces", () => {
    beforeEach(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariantNoProvinces));
    });

    it("shows empty state message", () => {
      renderWithRouter();
      expect(
        screen.getByText(/No provinces found. Please complete previous phases/)
      ).toBeInTheDocument();
    });
  });

  describe("without variant loaded", () => {
    it("returns null when no variant is loaded", () => {
      localStorage.clear();
      const { container } = renderWithRouter();
      expect(container.firstChild).toBeNull();
    });
  });
});
