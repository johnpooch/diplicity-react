import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LandingPage } from "@/components/LandingPage";
import { STORAGE_KEY } from "@/hooks/useVariant";
import * as exportModule from "@/utils/export";

vi.mock("@/utils/geometry", () => ({
  calculateCentroid: vi.fn(() => ({ x: 20, y: 20 })),
  calculatePositions: vi.fn(() => ({
    unitPosition: { x: 20, y: 20 },
    dislodgedUnitPosition: { x: 35, y: 35 },
    supplyCenterPosition: { x: 8, y: 8 },
  })),
}));

function renderWithRouter(ui: React.ReactElement, { route = "/" } = {}) {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);
}

const createMockFile = (content: string, name: string) => {
  const file = new File([content], name, { type: "image/svg+xml" });
  Object.defineProperty(file, "text", {
    value: () => Promise.resolve(content),
  });
  return file;
};

const createValidSvgFile = (provinceCount: number = 2) => {
  const paths = Array.from({ length: provinceCount }, (_, i) => {
    const x = i * 40;
    return `<path id="prov_${i}" d="M${x},10 L${x + 20},10 L${x + 20},30 L${x},30 Z"/>`;
  }).join("\n");

  const svgContent = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <g id="provinces">
        ${paths}
      </g>
    </svg>
  `;

  return createMockFile(svgContent, "test.svg");
};

const createInvalidSvgFile = () => {
  const svgContent = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <g id="background">
        <rect width="100" height="100"/>
      </g>
    </svg>
  `;
  return createMockFile(svgContent, "test.svg");
};

describe("LandingPage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders the Diplicity Variant Creator heading", () => {
    renderWithRouter(<LandingPage />);
    expect(screen.getByText("Diplicity Variant Creator")).toBeInTheDocument();
  });

  it("renders the file upload zone", () => {
    renderWithRouter(<LandingPage />);
    expect(
      screen.getByText("Drop SVG file here or click to upload")
    ).toBeInTheDocument();
  });

  it("shows map preview after valid SVG upload", async () => {
    renderWithRouter(<LandingPage />);

    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    const file = createValidSvgFile(3);

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("3 provinces detected")).toBeInTheDocument();
    });

    const svg = document.querySelector("svg[viewBox]");
    expect(svg).toBeInTheDocument();
  });

  it("does not show map after invalid SVG upload", async () => {
    renderWithRouter(<LandingPage />);

    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    const file = createInvalidSvgFile();

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(
        screen.getByText("SVG must contain a layer named 'provinces'")
      ).toBeInTheDocument();
    });

    expect(screen.queryByText(/provinces detected/)).not.toBeInTheDocument();
  });

  describe("persistence", () => {
    it("persists variant to localStorage after SVG upload", async () => {
      renderWithRouter(<LandingPage />);

      const input = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      const file = createValidSvgFile(3);

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("3 provinces detected")).toBeInTheDocument();
      });

      const saved = localStorage.getItem(STORAGE_KEY);
      expect(saved).not.toBeNull();
      const parsed = JSON.parse(saved!);
      expect(parsed.provinces).toHaveLength(3);
    });

    it("restores variant from localStorage on mount", () => {
      const mockVariant = {
        name: "test",
        description: "",
        author: "",
        version: "1.0.0",
        soloVictorySCCount: 0,
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
          {
            id: "p2",
            elementId: "p2",
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
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariant));

      renderWithRouter(<LandingPage />);

      expect(screen.getByText("2 provinces detected")).toBeInTheDocument();
    });

    it("shows Clear Draft button when variant exists", async () => {
      renderWithRouter(<LandingPage />);

      const input = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      const file = createValidSvgFile(2);

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /clear draft/i })
        ).toBeInTheDocument();
      });
    });

    it("clears variant when Clear Draft is clicked", async () => {
      renderWithRouter(<LandingPage />);

      const input = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      const file = createValidSvgFile(2);

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("2 provinces detected")).toBeInTheDocument();
      });

      const clearButton = screen.getByRole("button", { name: /clear draft/i });
      fireEvent.click(clearButton);

      expect(
        screen.queryByText("2 provinces detected")
      ).not.toBeInTheDocument();
      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });

    it("does not show Clear Draft button when no variant exists", () => {
      renderWithRouter(<LandingPage />);

      expect(
        screen.queryByRole("button", { name: /clear draft/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("JSON download", () => {
    beforeEach(() => {
      vi.spyOn(exportModule, "downloadVariantJson").mockImplementation(
        () => {}
      );
    });

    it("shows Download JSON button when variant exists", async () => {
      renderWithRouter(<LandingPage />);

      const input = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      const file = createValidSvgFile(2);

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /download json/i })
        ).toBeInTheDocument();
      });
    });

    it("does not show Download JSON button when no variant exists", () => {
      renderWithRouter(<LandingPage />);

      expect(
        screen.queryByRole("button", { name: /download json/i })
      ).not.toBeInTheDocument();
    });

    it("calls downloadVariantJson when Download JSON is clicked", async () => {
      renderWithRouter(<LandingPage />);

      const input = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      const file = createValidSvgFile(2);

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("2 provinces detected")).toBeInTheDocument();
      });

      const downloadButton = screen.getByRole("button", {
        name: /download json/i,
      });
      fireEvent.click(downloadButton);

      expect(exportModule.downloadVariantJson).toHaveBeenCalledTimes(1);
      expect(exportModule.downloadVariantJson).toHaveBeenCalledWith(
        expect.objectContaining({
          provinces: expect.any(Array),
        })
      );
    });
  });

  describe("Continue Editing", () => {
    it("shows Continue Editing button when variant exists", () => {
      const mockVariant = {
        name: "test",
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
      localStorage.setItem(STORAGE_KEY, JSON.stringify(mockVariant));

      renderWithRouter(<LandingPage />);

      expect(
        screen.getByRole("button", { name: /continue editing/i })
      ).toBeInTheDocument();
    });
  });
});
