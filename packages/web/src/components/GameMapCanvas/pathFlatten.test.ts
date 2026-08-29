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

  it("mirrors the previous cubic control point for a smooth cubic", () => {
    const smooth = flattenPath("M 0 0 C 0 10 10 10 10 0 S 20 -10 20 0");
    const explicit = flattenPath("M 0 0 C 0 10 10 10 10 0 C 10 -10 20 -10 20 0");
    expect(smooth[0]).toEqual(explicit[0]);
  });

  it("treats a smooth cubic with no preceding curve as starting flat", () => {
    const rings = flattenPath("M 0 0 S 10 10 20 0");
    const end = rings[0][rings[0].length - 1];
    expect(end.x).toBeCloseTo(20);
    expect(end.y).toBeCloseTo(0);
  });

  it("keeps later relative segments in place after a smooth cubic", () => {
    const rings = flattenPath("m 0 0 c 20 -40 60 -40 80 0 s 60 40 80 0 l 0 60 l -160 0 z");
    const xs = rings[0].map((point) => point.x);
    expect(Math.min(...xs)).toBeCloseTo(0);
    expect(Math.max(...xs)).toBeCloseTo(160);
  });

  it("samples a quadratic and mirrors it for a smooth quadratic", () => {
    const rings = flattenPath("M 0 0 Q 10 20 20 0 T 40 0");
    const ys = rings[0].map((point) => point.y);
    expect(Math.max(...ys)).toBeCloseTo(10);
    expect(Math.min(...ys)).toBeCloseTo(-10);
    const end = rings[0][rings[0].length - 1];
    expect(end.x).toBeCloseTo(40);
    expect(end.y).toBeCloseTo(0);
  });

  it("samples an elliptical arc along its sweep", () => {
    const rings = flattenPath("M 0 0 A 10 10 0 0 1 20 0");
    const ys = rings[0].map((point) => point.y);
    expect(Math.min(...ys)).toBeCloseTo(-10);
    expect(Math.max(...ys)).toBeCloseTo(0);
    const end = rings[0][rings[0].length - 1];
    expect(end).toEqual({ x: 20, y: 0 });
  });

  it("sweeps an arc the other way when the sweep flag is clear", () => {
    const rings = flattenPath("M 0 0 A 10 10 0 0 0 20 0");
    const ys = rings[0].map((point) => point.y);
    expect(Math.max(...ys)).toBeCloseTo(10);
  });

  it("reads arc flags packed against the following coordinate", () => {
    const packed = flattenPath("M 0 0 A 10 10 0 0120 0");
    const spaced = flattenPath("M 0 0 A 10 10 0 0 1 20 0");
    expect(packed[0]).toEqual(spaced[0]);
  });

  it("scales up arc radii that are too small to span the endpoints", () => {
    const rings = flattenPath("M 0 0 A 1 1 0 0 1 20 0");
    const end = rings[0][rings[0].length - 1];
    expect(end).toEqual({ x: 20, y: 0 });
  });

  it("terminates on a stray coordinate after a closepath", () => {
    const rings = flattenPath("M 0 0 L 10 0 L 10 10 Z 5 5");
    expect(rings).toHaveLength(1);
  });
});
