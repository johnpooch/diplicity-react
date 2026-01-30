import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PhaseProvinces } from "../PhaseProvinces";
import { STORAGE_KEY } from "@/hooks/useVariant";

vi.mock("@/utils/geometry", () => ({
  calculateCentroid: vi.fn(() => ({ x: 20, y: 20 })),
  calculatePositions: vi.fn(() => ({
    unitPosition: { x: 20, y: 20 },
    dislodgedUnitPosition: { x: 35, y: 35 },
    supplyCenterPosition: { x: 8, y: 8 },
  })),
}));

const mockVariant = {
  name: "Test Variant",
  description: "",
  author: "",
  version: "1.0.0",
  soloVictorySCCount: 18,
  nations: [
    { id: "england", name: "England", color: "#2196F3" },
    { id: "france", name: "France", color: "#F44336" },
  ],
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
    {
      id: "nth",
      elementId: "province-3",
      name: "North Sea",
      type: "sea" as const,
      path: "M70,10 L90,10 L90,30 L70,30 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 80, y: 20 },
      dislodgedUnitPosition: { x: 95, y: 35 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
};

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <PhaseProvinces />
    </MemoryRouter>
  );
}

describe("PhaseProvinces", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariant));
  });

  it("renders province details section", () => {
    renderWithRouter();
    expect(screen.getByText("Province Details")).toBeInTheDocument();
  });

  it("displays all provinces in the table", () => {
    renderWithRouter();
    expect(screen.getByDisplayValue("Berlin")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Munich")).toBeInTheDocument();
    expect(screen.getByDisplayValue("North Sea")).toBeInTheDocument();
  });

  it("displays province IDs", () => {
    renderWithRouter();
    expect(screen.getByDisplayValue("ber")).toBeInTheDocument();
    expect(screen.getByDisplayValue("mun")).toBeInTheDocument();
    expect(screen.getByDisplayValue("nth")).toBeInTheDocument();
  });

  it("shows progress count", () => {
    renderWithRouter();
    expect(screen.getByText(/3 of 3 complete/)).toBeInTheDocument();
  });

  it("allows editing province name", async () => {
    renderWithRouter();

    const berlinInput = screen.getByDisplayValue("Berlin");
    fireEvent.change(berlinInput, { target: { value: "Brandenburg" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Brandenburg")).toBeInTheDocument();
    });
  });

  it("allows editing province ID", async () => {
    renderWithRouter();

    const idInput = screen.getByDisplayValue("ber");
    fireEvent.change(idInput, { target: { value: "bra" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("bra")).toBeInTheDocument();
    });
  });

  it("persists province changes to localStorage", async () => {
    renderWithRouter();

    const nameInput = screen.getByDisplayValue("Berlin");
    fireEvent.change(nameInput, { target: { value: "Brandenburg" } });

    await waitFor(() => {
      const saved = localStorage.getItem(STORAGE_KEY);
      const parsed = JSON.parse(saved!);
      const province = parsed.provinces.find(
        (p: { elementId: string }) => p.elementId === "province-1"
      );
      expect(province.name).toBe("Brandenburg");
    });
  });

  it("shows validation error for duplicate IDs", async () => {
    renderWithRouter();

    const munIdInput = screen.getByDisplayValue("mun");
    fireEvent.change(munIdInput, { target: { value: "ber" } });

    await waitFor(
      () => {
        const errors = screen.getAllByText(/ID must be unique/i);
        expect(errors.length).toBeGreaterThanOrEqual(1);
      },
      { timeout: 2000 }
    );
  });

  it("shows validation error for invalid ID format", async () => {
    renderWithRouter();

    const idInput = screen.getByDisplayValue("ber");
    fireEvent.change(idInput, { target: { value: "be" } });

    await waitFor(
      () => {
        const errors = screen.getAllByText(/ID must be exactly 3 characters/i);
        expect(errors.length).toBeGreaterThanOrEqual(1);
      },
      { timeout: 2000 }
    );
  });

  it("renders the map with provinces", () => {
    renderWithRouter();

    const svg = document.querySelector("svg");
    expect(svg).toBeInTheDocument();

    const paths = document.querySelectorAll("path");
    expect(paths.length).toBeGreaterThanOrEqual(3);
  });

  it("shows selected province info when clicked", async () => {
    renderWithRouter();

    const berlinRow = screen.getByDisplayValue("Berlin").closest("tr");
    fireEvent.click(berlinRow!);

    await waitFor(() => {
      expect(screen.getByText(/Selected:/)).toBeInTheDocument();
      expect(screen.getByText(/Berlin/)).toBeInTheDocument();
    });
  });

  it("returns null when no variant is loaded", () => {
    localStorage.clear();
    const { container } = renderWithRouter();
    expect(container.firstChild).toBeNull();
  });
});
