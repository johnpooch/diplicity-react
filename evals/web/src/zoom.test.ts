import { describe, expect, test } from "vitest";
import { IDENTITY, MAX_SCALE, panBy, wheelFactor, zoomAt } from "./zoom";

const size = { width: 400, height: 300 };

describe("zoomAt", () => {
  test("keeps the point under the cursor fixed", () => {
    const view = zoomAt(IDENTITY, size, 100, 50, 2);
    expect(view).toEqual({ scale: 2, x: -100, y: -50 });
    expect((100 - view.x) / view.scale).toBe(100);
    expect((50 - view.y) / view.scale).toBe(50);
  });

  test("never zooms out past the whole board", () => {
    expect(zoomAt(IDENTITY, size, 100, 50, 0.5)).toEqual(IDENTITY);
  });

  test("never zooms in past the maximum scale", () => {
    expect(zoomAt(IDENTITY, size, 0, 0, 100).scale).toBe(MAX_SCALE);
  });
});

describe("panBy", () => {
  test("cannot move the board away from the edges", () => {
    const view = zoomAt(IDENTITY, size, 0, 0, 2);
    expect(panBy(view, size, 50, 50)).toEqual({ scale: 2, x: 0, y: 0 });
    expect(panBy(view, size, -1000, -1000)).toEqual({ scale: 2, x: -400, y: -300 });
  });

  test("does nothing at the whole-board view", () => {
    expect(panBy(IDENTITY, size, -50, 20)).toEqual(IDENTITY);
  });
});

describe("wheelFactor", () => {
  test("scrolling up zooms in and down zooms out", () => {
    expect(wheelFactor(-10)).toBeGreaterThan(1);
    expect(wheelFactor(10)).toBeLessThan(1);
  });

  test("caps a single large wheel step", () => {
    expect(wheelFactor(-10000)).toBe(Math.exp(0.5));
  });
});
