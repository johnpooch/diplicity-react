import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("paper", () => {
  const mockPath = vi.fn().mockImplementation((pathD: string) => {
    const coordMatch = pathD.match(/M(\d+),(\d+)/);
    const sizeMatch = pathD.match(/L(\d+),\d+ L\d+,(\d+)/);

    if (coordMatch && sizeMatch) {
      const x1 = parseInt(coordMatch[1], 10);
      const y1 = parseInt(coordMatch[2], 10);
      const x2 = parseInt(sizeMatch[1], 10);
      const y2 = parseInt(sizeMatch[2], 10);

      return {
        bounds: {
          center: {
            x: (x1 + x2) / 2,
            y: (y1 + y2) / 2,
          },
        },
      };
    }

    return {
      bounds: {
        center: { x: 50, y: 50 },
      },
    };
  });

  return {
    default: {
      setup: vi.fn(),
      Size: vi.fn(),
      Path: mockPath,
    },
  };
});

import { calculateCentroid, calculatePositions } from "../geometry";

describe("calculateCentroid", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns correct center for simple square", () => {
    const pathD = "M10,10 L30,10 L30,30 L10,30 Z";
    const centroid = calculateCentroid(pathD);
    expect(centroid.x).toBe(20);
    expect(centroid.y).toBe(20);
  });

  it("returns correct center for rectangle", () => {
    const pathD = "M0,0 L100,0 L100,50 L0,50 Z";
    const centroid = calculateCentroid(pathD);
    expect(centroid.x).toBe(50);
    expect(centroid.y).toBe(25);
  });

  it("handles complex path and returns a position", () => {
    const pathD = "M50,10 L90,40 L75,90 L25,90 L10,40 Z";
    const centroid = calculateCentroid(pathD);
    expect(typeof centroid.x).toBe("number");
    expect(typeof centroid.y).toBe("number");
  });
});

describe("calculatePositions", () => {
  it("applies correct offsets", () => {
    const centroid = { x: 100, y: 100 };
    const positions = calculatePositions(centroid);

    expect(positions.unitPosition).toEqual({ x: 100, y: 100 });
    expect(positions.dislodgedUnitPosition).toEqual({ x: 115, y: 115 });
    expect(positions.supplyCenterPosition).toEqual({ x: 88, y: 88 });
  });

  it("preserves centroid values for unit position", () => {
    const centroid = { x: 50, y: 75 };
    const positions = calculatePositions(centroid);

    expect(positions.unitPosition).toEqual(centroid);
  });
});
