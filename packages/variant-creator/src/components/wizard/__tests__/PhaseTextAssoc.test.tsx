import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PhaseTextAssoc } from "../PhaseTextAssoc";
import { STORAGE_KEY } from "@/hooks/useVariant";

vi.mock("@/utils/geometry", () => ({
  calculateCentroid: vi.fn((path: string) => {
    if (path.includes("10,10")) return { x: 20, y: 20 };
    if (path.includes("40,10")) return { x: 50, y: 20 };
    return { x: 80, y: 20 };
  }),
  calculatePositions: vi.fn(() => ({
    unitPosition: { x: 20, y: 20 },
    dislodgedUnitPosition: { x: 35, y: 35 },
    supplyCenterPosition: { x: 8, y: 8 },
  })),
}));

const mockVariantWithText = {
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
      path: "M40,10 L60,10 L60,30 L40,30 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 50, y: 20 },
      dislodgedUnitPosition: { x: 65, y: 35 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
  textElements: [
    { content: "Berlin", x: 20, y: 20 },
    { content: "Munich", x: 50, y: 20 },
    { content: "Far Away", x: 500, y: 500 },
  ],
};

const mockVariantNoText = {
  ...mockVariantWithText,
  textElements: [],
};

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <PhaseTextAssoc />
    </MemoryRouter>
  );
}

describe("PhaseTextAssoc", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("with text elements", () => {
    beforeEach(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariantWithText));
    });

    it("renders text association section", () => {
      renderWithRouter();
      expect(screen.getByText("Text Association")).toBeInTheDocument();
    });

    it("displays all text elements in the table", () => {
      renderWithRouter();
      expect(screen.getAllByText("Berlin").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Munich").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Far Away").length).toBeGreaterThanOrEqual(1);
    });

    it("shows association count", () => {
      renderWithRouter();
      expect(screen.getByText(/0 of 3 texts associated/)).toBeInTheDocument();
    });

    it("renders the map with provinces", () => {
      renderWithRouter();

      const svg = document.querySelector("svg");
      expect(svg).toBeInTheDocument();

      const paths = document.querySelectorAll("path");
      expect(paths.length).toBeGreaterThanOrEqual(2);
    });

    it("renders auto-detect button", () => {
      renderWithRouter();
      expect(screen.getByText("Auto-Detect")).toBeInTheDocument();
    });

    it("auto-detects associations based on proximity", async () => {
      renderWithRouter();

      const autoDetectButton = screen.getByText("Auto-Detect");
      fireEvent.click(autoDetectButton);

      await waitFor(() => {
        expect(screen.getByText(/2 of 3 texts associated/)).toBeInTheDocument();
      });
    });

    it("allows selecting a text element from the table", async () => {
      renderWithRouter();

      const berlinCells = screen.getAllByText("Berlin");
      const tableCell = berlinCells.find((el) => el.closest("td"));
      const firstRow = tableCell?.closest("tr");
      fireEvent.click(firstRow!);

      await waitFor(() => {
        expect(screen.getByText(/Selected text:/)).toBeInTheDocument();
      });
    });

    it("persists associations to localStorage", async () => {
      renderWithRouter();

      const autoDetectButton = screen.getByText("Auto-Detect");
      fireEvent.click(autoDetectButton);

      await waitFor(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        const parsed = JSON.parse(saved!);
        const berlinProvince = parsed.provinces.find(
          (p: { id: string }) => p.id === "ber"
        );
        expect(berlinProvince.labels.length).toBeGreaterThan(0);
        expect(berlinProvince.labels[0].text).toBe("Berlin");
        expect(berlinProvince.labels[0].source).toBe("svg");
      });
    });

    it("shows province dropdown for each text", () => {
      renderWithRouter();

      const triggers = screen.getAllByRole("combobox");
      expect(triggers.length).toBe(3);
    });

    it("clears association when clear button is clicked", async () => {
      renderWithRouter();

      const autoDetectButton = screen.getByText("Auto-Detect");
      fireEvent.click(autoDetectButton);

      await waitFor(() => {
        expect(screen.getByText(/2 of 3 texts associated/)).toBeInTheDocument();
      });

      const clearButtons = screen.getAllByRole("button", { name: "" });
      const enabledClearButton = clearButtons.find(
        (btn) => !btn.hasAttribute("disabled")
      );

      if (enabledClearButton) {
        fireEvent.click(enabledClearButton);

        await waitFor(() => {
          expect(screen.getByText(/1 of 3 texts associated/)).toBeInTheDocument();
        });
      }
    });
  });

  describe("without text elements", () => {
    beforeEach(() => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariantNoText));
    });

    it("shows empty state message", () => {
      renderWithRouter();
      expect(
        screen.getByText(/No text elements found in the SVG/)
      ).toBeInTheDocument();
    });

    it("indicates user can proceed to next phase", () => {
      renderWithRouter();
      expect(
        screen.getByText(/You can proceed to the next phase/)
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
