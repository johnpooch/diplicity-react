import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";

vi.mock("@/utils/geometry", () => ({
  calculateCentroid: vi.fn(() => ({ x: 20, y: 20 })),
  calculatePositions: vi.fn(() => ({
    unitPosition: { x: 20, y: 20 },
    dislodgedUnitPosition: { x: 35, y: 35 },
    supplyCenterPosition: { x: 8, y: 8 },
  })),
}));

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

describe("App", () => {
  it("renders the Diplicity Variant Creator heading", () => {
    render(<App />);
    expect(screen.getByText("Diplicity Variant Creator")).toBeInTheDocument();
  });

  it("renders the file upload zone", () => {
    render(<App />);
    expect(
      screen.getByText("Drop SVG file here or click to upload")
    ).toBeInTheDocument();
  });

  it("shows map preview after valid SVG upload", async () => {
    render(<App />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createValidSvgFile(3);

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("3 provinces detected")).toBeInTheDocument();
    });

    const svg = document.querySelector("svg[viewBox]");
    expect(svg).toBeInTheDocument();
  });

  it("does not show map after invalid SVG upload", async () => {
    render(<App />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = createInvalidSvgFile();

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(
        screen.getByText("SVG must contain a layer named 'provinces'")
      ).toBeInTheDocument();
    });

    expect(screen.queryByText(/provinces detected/)).not.toBeInTheDocument();
  });
});
