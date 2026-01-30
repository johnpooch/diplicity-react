import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PhaseVisualEditor } from "../PhaseVisualEditor";
import { STORAGE_KEY } from "@/hooks/useVariant";

vi.mock("@/utils/geometry", () => ({
  calculateCentroid: vi.fn(() => ({ x: 20, y: 20 })),
  calculatePositions: vi.fn(() => ({
    unitPosition: { x: 20, y: 20 },
    dislodgedUnitPosition: { x: 35, y: 35 },
    supplyCenterPosition: { x: 8, y: 8 },
  })),
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
      path: "M10,10 L30,10 L30,30 L10,30 Z",
      homeNation: "england",
      supplyCenter: true,
      startingUnit: { type: "Army" as const },
      adjacencies: ["mun"],
      labels: [
        {
          text: "Berlin",
          position: { x: 20, y: 20 },
          rotation: 0,
          source: "svg" as const,
          styles: {},
        },
      ],
      unitPosition: { x: 20, y: 20 },
      dislodgedUnitPosition: { x: 35, y: 35 },
      supplyCenterPosition: { x: 8, y: 8 },
    },
    {
      id: "mun",
      elementId: "province-2",
      name: "Munich",
      type: "land" as const,
      path: "M40,10 L60,10 L60,30 L40,30 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: ["ber"],
      labels: [
        {
          text: "Munich",
          position: { x: 50, y: 20 },
          rotation: 0,
          source: "svg" as const,
          styles: {},
        },
      ],
      unitPosition: { x: 50, y: 20 },
      dislodgedUnitPosition: { x: 65, y: 35 },
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
      <PhaseVisualEditor />
    </MemoryRouter>
  );
}

describe("PhaseVisualEditor", () => {
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

    it("renders visual editor section", () => {
      renderWithRouter();
      expect(screen.getByText("Visual Editor")).toBeInTheDocument();
    });

    it("renders visibility toggle checkboxes", () => {
      renderWithRouter();
      expect(screen.getByLabelText("Units")).toBeInTheDocument();
      expect(screen.getByLabelText("Dislodged")).toBeInTheDocument();
      expect(screen.getByLabelText("Supply Centers")).toBeInTheDocument();
      expect(screen.getByLabelText("Labels")).toBeInTheDocument();
    });

    it("renders the map with provinces", () => {
      renderWithRouter();

      const svg = document.querySelector("svg");
      expect(svg).toBeInTheDocument();

      const paths = document.querySelectorAll("path");
      expect(paths.length).toBeGreaterThanOrEqual(2);
    });

    it("renders unit markers for provinces with starting units", () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      expect(circles.length).toBeGreaterThan(0);
    });

    it("renders supply center markers for SC provinces", () => {
      renderWithRouter();

      const polygons = document.querySelectorAll("polygon");
      expect(polygons.length).toBeGreaterThanOrEqual(1);
    });

    it("renders label text elements", () => {
      renderWithRouter();

      expect(screen.getByText("Berlin")).toBeInTheDocument();
      expect(screen.getByText("Munich")).toBeInTheDocument();
    });

    it("toggles unit visibility when checkbox is clicked", async () => {
      renderWithRouter();

      const unitsCheckbox = screen.getByLabelText("Units");
      const initialCircleCount = document.querySelectorAll("circle").length;

      fireEvent.click(unitsCheckbox);

      await waitFor(() => {
        const newCircleCount = document.querySelectorAll("circle").length;
        expect(newCircleCount).toBeLessThan(initialCircleCount);
      });
    });

    it("toggles supply center visibility when checkbox is clicked", async () => {
      renderWithRouter();

      const scCheckbox = screen.getByLabelText("Supply Centers");
      const initialPolygonCount = document.querySelectorAll("polygon").length;

      fireEvent.click(scCheckbox);

      await waitFor(() => {
        const newPolygonCount = document.querySelectorAll("polygon").length;
        expect(newPolygonCount).toBeLessThan(initialPolygonCount);
      });
    });

    it("toggles label visibility when checkbox is clicked", async () => {
      renderWithRouter();

      expect(screen.getByText("Berlin")).toBeInTheDocument();

      const labelsCheckbox = screen.getByLabelText("Labels");
      fireEvent.click(labelsCheckbox);

      await waitFor(() => {
        expect(screen.queryByText("Berlin")).not.toBeInTheDocument();
      });
    });

    it("shows selection panel when clicking a marker", async () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      expect(circles.length).toBeGreaterThan(0);

      fireEvent.click(circles[0]);

      await waitFor(() => {
        expect(screen.getByText("Unit Position")).toBeInTheDocument();
      });
    });

    it("shows Reset to Auto button in selection panel", async () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      fireEvent.click(circles[0]);

      await waitFor(() => {
        expect(screen.getByText("Reset to Auto")).toBeInTheDocument();
      });
    });

    it("shows X and Y inputs in selection panel", async () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      fireEvent.click(circles[0]);

      await waitFor(() => {
        expect(screen.getByLabelText("X")).toBeInTheDocument();
        expect(screen.getByLabelText("Y")).toBeInTheDocument();
      });
    });

    it("shows rotation input when label is selected", async () => {
      renderWithRouter();

      const labelTexts = document.querySelectorAll(".label-layer text");
      expect(labelTexts.length).toBeGreaterThan(0);

      fireEvent.click(labelTexts[0]);

      await waitFor(() => {
        expect(screen.getByLabelText("Rotation (degrees)")).toBeInTheDocument();
      });
    });

    it("deselects element when clicking on a province path", async () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      fireEvent.click(circles[0]);

      await waitFor(() => {
        expect(screen.getByText("Unit Position")).toBeInTheDocument();
      });

      const provincePaths = document.querySelectorAll(".province-layer path");
      fireEvent.click(provincePaths[0]);

      await waitFor(() => {
        expect(screen.queryByText("Unit Position")).not.toBeInTheDocument();
      });
    });

    it("updates position when X input is changed", async () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      fireEvent.click(circles[0]);

      await waitFor(() => {
        expect(screen.getByLabelText("X")).toBeInTheDocument();
      });

      const xInput = screen.getByLabelText("X");
      fireEvent.change(xInput, { target: { value: "100" } });

      await waitFor(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        const parsed = JSON.parse(saved!);
        expect(parsed.provinces[0].unitPosition.x).toBe(100);
      });
    });

    it("resets position when Reset to Auto is clicked", async () => {
      renderWithRouter();

      const circles = document.querySelectorAll("circle");
      fireEvent.click(circles[0]);

      await waitFor(() => {
        expect(screen.getByText("Reset to Auto")).toBeInTheDocument();
      });

      const xInput = screen.getByLabelText("X");
      fireEvent.change(xInput, { target: { value: "150" } });

      await waitFor(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        const parsed = JSON.parse(saved!);
        expect(parsed.provinces[0].unitPosition.x).toBe(150);
      });

      const resetButton = screen.getByText("Reset to Auto");
      fireEvent.click(resetButton);

      await waitFor(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        const parsed = JSON.parse(saved!);
        expect(parsed.provinces[0].unitPosition.x).toBe(20);
      });
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
