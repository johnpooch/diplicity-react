import { describe, it, expect } from "vitest";
import { decimate } from "./decimate";
import type { Point } from "../InteractiveMap/dsvgParser";

describe("decimate", () => {
  it("returns the input unchanged when there are two or fewer points", () => {
    const points: Point[] = [
      { x: 0, y: 0 },
      { x: 10, y: 10 },
    ];
    expect(decimate(points, 5)).toEqual(points);
  });

  it("collapses collinear points to the two endpoints", () => {
    const points: Point[] = [
      { x: 0, y: 0 },
      { x: 1, y: 0 },
      { x: 2, y: 0 },
      { x: 3, y: 0 },
    ];
    expect(decimate(points, 0.001)).toEqual([
      { x: 0, y: 0 },
      { x: 3, y: 0 },
    ]);
  });

  it("keeps a vertex that deviates beyond the tolerance", () => {
    const points: Point[] = [
      { x: 0, y: 0 },
      { x: 5, y: 10 },
      { x: 10, y: 0 },
    ];
    expect(decimate(points, 1)).toEqual(points);
  });

  it("drops a vertex whose deviation is within the tolerance", () => {
    const points: Point[] = [
      { x: 0, y: 0 },
      { x: 5, y: 0.5 },
      { x: 10, y: 0 },
    ];
    expect(decimate(points, 1)).toEqual([
      { x: 0, y: 0 },
      { x: 10, y: 0 },
    ]);
  });

  it("simplifies a dense near-straight ring while preserving real corners", () => {
    const points: Point[] = [
      { x: 0, y: 0 },
      { x: 2, y: 0.1 },
      { x: 4, y: -0.1 },
      { x: 6, y: 0 },
      { x: 6, y: 20 },
      { x: 0, y: 20 },
    ];
    const simplified = decimate(points, 1);
    expect(simplified).toEqual([
      { x: 0, y: 0 },
      { x: 6, y: 0 },
      { x: 6, y: 20 },
      { x: 0, y: 20 },
    ]);
    expect(simplified.length).toBeLessThan(points.length);
  });
});
