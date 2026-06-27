import { describe, it, expect } from "vitest";
import { flattenPath } from "./pathFlatten";

describe("flattenPath", () => {
  it("flattens an absolute M/L/Z triangle into a closed ring", () => {
    const rings = flattenPath("M 0 0 L 10 0 L 10 10 Z");
    expect(rings).toHaveLength(1);
    expect(rings[0]).toEqual([
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 10, y: 10 },
      { x: 0, y: 0 },
    ]);
  });

  it("resolves relative commands and implicit lineto after moveto", () => {
    const rings = flattenPath("m 1 1 2 0 0 2 z");
    expect(rings[0]).toEqual([
      { x: 1, y: 1 },
      { x: 3, y: 1 },
      { x: 3, y: 3 },
      { x: 1, y: 1 },
    ]);
  });

  it("supports horizontal and vertical commands", () => {
    const rings = flattenPath("M 0 0 H 5 V 5 H 0 Z");
    expect(rings[0]).toEqual([
      { x: 0, y: 0 },
      { x: 5, y: 0 },
      { x: 5, y: 5 },
      { x: 0, y: 5 },
      { x: 0, y: 0 },
    ]);
  });

  it("samples a cubic into multiple line segments ending at the curve end", () => {
    const rings = flattenPath("M 0 0 C 0 10 10 10 10 0");
    expect(rings[0][0]).toEqual({ x: 0, y: 0 });
    expect(rings[0].length).toBeGreaterThan(2);
    const end = rings[0][rings[0].length - 1];
    expect(end.x).toBeCloseTo(10);
    expect(end.y).toBeCloseTo(0);
  });

  it("splits each moveto into its own ring", () => {
    const rings = flattenPath("M 0 0 L 1 0 Z M 5 5 L 6 5 Z");
    expect(rings).toHaveLength(2);
    expect(rings[0][0]).toEqual({ x: 0, y: 0 });
    expect(rings[1][0]).toEqual({ x: 5, y: 5 });
  });
});
