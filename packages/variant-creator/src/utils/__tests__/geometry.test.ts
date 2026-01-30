import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("paper", () => {
  const mockPath = vi.fn().mockImplementation((pathD: string) => {
    const coordMatch = pathD.match(/M(\d+),(\d+)/);
    const sizeMatch = pathD.match(/L(\d+),\d+ L\d+,(\d+)/);

    const pathObj = {
      pathD,
      bounds: {
        center: { x: 50, y: 50 },
      },
      getIntersections: vi.fn().mockImplementation((other: { pathD: string }) => {
        const thisPath = pathD;
        const otherPath = other.pathD;

        if (thisPath.includes("adjacent") && otherPath.includes("adjacent")) {
          return [{}, {}];
        }
        if (thisPath.includes("corner") && otherPath.includes("corner")) {
          return [{}];
        }
        return [];
      }),
    };

    if (coordMatch && sizeMatch) {
      const x1 = parseInt(coordMatch[1], 10);
      const y1 = parseInt(coordMatch[2], 10);
      const x2 = parseInt(sizeMatch[1], 10);
      const y2 = parseInt(sizeMatch[2], 10);

      pathObj.bounds.center = {
        x: (x1 + x2) / 2,
        y: (y1 + y2) / 2,
      };
    }

    return pathObj;
  });

  return {
    default: {
      setup: vi.fn(),
      Size: vi.fn(),
      Path: mockPath,
    },
  };
});

import {
  calculateCentroid,
  calculatePositions,
  detectPathIntersections,
} from "../geometry";

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

describe("detectPathIntersections", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns true for paths that share a border (2+ intersections)", () => {
    const pathA = "M0,0 adjacent L10,0 L10,10 L0,10 Z";
    const pathB = "M10,0 adjacent L20,0 L20,10 L10,10 Z";
    const result = detectPathIntersections(pathA, pathB);
    expect(result).toBe(true);
  });

  it("returns false for paths that only touch at a corner (1 intersection)", () => {
    const pathA = "M0,0 corner L10,0 L10,10 L0,10 Z";
    const pathB = "M10,10 corner L20,10 L20,20 L10,20 Z";
    const result = detectPathIntersections(pathA, pathB);
    expect(result).toBe(false);
  });

  it("returns false for non-touching paths (0 intersections)", () => {
    const pathA = "M0,0 L10,0 L10,10 L0,10 Z";
    const pathB = "M100,100 L110,100 L110,110 L100,110 Z";
    const result = detectPathIntersections(pathA, pathB);
    expect(result).toBe(false);
  });
});
