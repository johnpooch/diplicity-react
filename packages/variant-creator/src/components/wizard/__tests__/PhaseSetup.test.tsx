import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PhaseSetup } from "../PhaseSetup";
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
  name: "",
  description: "",
  author: "",
  version: "1.0.0",
  soloVictorySCCount: 18,
  nations: [],
  provinces: [
    {
      id: "p1",
      elementId: "p1",
      name: "",
      type: "land",
      path: "M0,0",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 0, y: 0 },
      dislodgedUnitPosition: { x: 0, y: 0 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
};

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <PhaseSetup />
    </MemoryRouter>
  );
}

describe("PhaseSetup", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariant));
  });

  it("renders variant information section", () => {
    renderWithRouter();
    expect(screen.getByText("Variant Information")).toBeInTheDocument();
  });

  it("renders nations section", () => {
    renderWithRouter();
    expect(screen.getByText("Nations")).toBeInTheDocument();
  });

  it("displays variant name input", () => {
    renderWithRouter();
    expect(screen.getByLabelText(/variant name/i)).toBeInTheDocument();
  });

  it("displays description textarea", () => {
    renderWithRouter();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it("displays author input", () => {
    renderWithRouter();
    expect(screen.getByLabelText(/author/i)).toBeInTheDocument();
  });

  it("displays solo victory SC count input", () => {
    renderWithRouter();
    expect(screen.getByLabelText(/solo victory sc count/i)).toBeInTheDocument();
  });

  it("starts with 2 nation rows by default", () => {
    renderWithRouter();
    const nationInputs = screen.getAllByPlaceholderText(/nation name/i);
    expect(nationInputs).toHaveLength(2);
  });

  it("allows adding new nations", async () => {
    renderWithRouter();

    const addButton = screen.getByRole("button", { name: /add nation/i });
    fireEvent.click(addButton);

    const nationInputs = screen.getAllByPlaceholderText(/nation name/i);
    expect(nationInputs).toHaveLength(3);
  });

  it("allows removing nations when more than 2 exist", async () => {
    renderWithRouter();

    const addButton = screen.getByRole("button", { name: /add nation/i });
    fireEvent.click(addButton);

    const removeButtons = screen.getAllByRole("button", {
      name: /remove nation/i,
    });
    expect(removeButtons).toHaveLength(3);

    fireEvent.click(removeButtons[0]);

    await waitFor(() => {
      const nationInputs = screen.getAllByPlaceholderText(/nation name/i);
      expect(nationInputs).toHaveLength(2);
    });
  });

  it("disables remove button when only 2 nations exist", () => {
    renderWithRouter();

    const removeButtons = screen.getAllByRole("button", {
      name: /remove nation/i,
    });
    removeButtons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it("validates that variant name is required", async () => {
    renderWithRouter();

    const nameInput = screen.getByLabelText(/variant name/i);
    fireEvent.change(nameInput, { target: { value: "test" } });
    fireEvent.change(nameInput, { target: { value: "" } });
    fireEvent.blur(nameInput);

    await waitFor(
      () => {
        expect(
          screen.getByText(/variant name is required/i)
        ).toBeInTheDocument();
      },
      { timeout: 2000 }
    );
  });

  it("validates solo victory SC count must be at least 1", async () => {
    renderWithRouter();

    const scInput = screen.getByLabelText(/solo victory sc count/i);
    fireEvent.change(scInput, { target: { value: "0" } });
    fireEvent.blur(scInput);

    await waitFor(() => {
      expect(screen.getByText(/must be at least 1/i)).toBeInTheDocument();
    });
  });

  it("persists metadata changes to localStorage", async () => {
    renderWithRouter();

    const nameInput = screen.getByLabelText(/variant name/i);
    fireEvent.change(nameInput, { target: { value: "Test Variant" } });

    await waitFor(() => {
      const saved = localStorage.getItem(STORAGE_KEY);
      const parsed = JSON.parse(saved!);
      expect(parsed.name).toBe("Test Variant");
    });
  });

  it("persists nation changes to localStorage", async () => {
    renderWithRouter();

    const nationInputs = screen.getAllByPlaceholderText(/nation name/i);
    fireEvent.change(nationInputs[0], { target: { value: "England" } });
    fireEvent.change(nationInputs[1], { target: { value: "France" } });

    await waitFor(
      () => {
        const saved = localStorage.getItem(STORAGE_KEY);
        const parsed = JSON.parse(saved!);
        expect(parsed.nations.length).toBeGreaterThanOrEqual(1);
        const nationNames = parsed.nations.map(
          (n: { name: string }) => n.name
        );
        expect(nationNames).toContain("England");
      },
      { timeout: 2000 }
    );
  });

  it("loads existing variant data into form", () => {
    const existingVariant = {
      ...mockVariant,
      name: "Existing Variant",
      description: "Test description",
      author: "Test Author",
      soloVictorySCCount: 22,
      nations: [
        { id: "eng", name: "England", color: "#2196F3" },
        { id: "fra", name: "France", color: "#00BCD4" },
      ],
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(existingVariant));

    renderWithRouter();

    expect(screen.getByDisplayValue("Existing Variant")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test description")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test Author")).toBeInTheDocument();
    expect(screen.getByDisplayValue("22")).toBeInTheDocument();
    expect(screen.getByDisplayValue("England")).toBeInTheDocument();
    expect(screen.getByDisplayValue("France")).toBeInTheDocument();
  });
});
