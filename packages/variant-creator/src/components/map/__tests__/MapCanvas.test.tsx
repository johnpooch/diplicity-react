import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MapCanvas } from "../MapCanvas";
import type { VariantDefinition } from "@/types/variant";

const createTestVariant = (
  overrides: Partial<VariantDefinition> = {}
): VariantDefinition => ({
  name: "Test Variant",
  description: "",
  author: "",
  version: "1.0.0",
  soloVictorySCCount: 18,
  nations: [],
  provinces: [
    {
      id: "ber",
      elementId: "ber",
      name: "Berlin",
      type: "land",
      path: "M10,10 L30,10 L30,30 L10,30 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 20, y: 20 },
      dislodgedUnitPosition: { x: 35, y: 35 },
      supplyCenterPosition: { x: 8, y: 8 },
    },
    {
      id: "mun",
      elementId: "mun",
      name: "Munich",
      type: "land",
      path: "M40,10 L60,10 L60,30 L40,30 Z",
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: { x: 50, y: 20 },
      dislodgedUnitPosition: { x: 65, y: 35 },
      supplyCenterPosition: { x: 38, y: 8 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
  ...overrides,
});

describe("MapCanvas", () => {
  it("renders SVG with correct viewBox", () => {
    const variant = createTestVariant({
      dimensions: { width: 1524, height: 1357 },
    });

    const { container } = render(<MapCanvas variant={variant} />);
    const svg = container.querySelector("svg");

    expect(svg).toHaveAttribute("viewBox", "0 0 1524 1357");
  });

  it("renders province paths", () => {
    const variant = createTestVariant();

    const { container } = render(<MapCanvas variant={variant} />);
    const paths = container.querySelectorAll("path");

    expect(paths).toHaveLength(2);
  });

  it("renders decorative elements", () => {
    const variant = createTestVariant({
      decorativeElements: [
        {
          id: "background",
          type: "group",
          content: '<rect width="100" height="100" fill="blue" data-testid="bg"/>',
        },
      ],
    });

    const { container } = render(<MapCanvas variant={variant} />);
    const rect = container.querySelector("rect");

    expect(rect).toBeInTheDocument();
    expect(rect).toHaveAttribute("fill", "blue");
  });

  it("handles empty provinces", () => {
    const variant = createTestVariant({ provinces: [] });

    const { container } = render(<MapCanvas variant={variant} />);
    const svg = container.querySelector("svg");

    expect(svg).toBeInTheDocument();
  });
});
