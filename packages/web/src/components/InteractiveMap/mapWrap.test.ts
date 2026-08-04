import { describe, expect, it } from "vitest";
import {
  nearestWorldCopyIndex,
  wrappedPointNear,
  wrappedXNear,
} from "./mapWrap";

describe("wrappedXNear", () => {
  it("moves a point across the right seam when that is the shortest route", () => {
    expect(wrappedXNear(100, 900, 1000)).toBe(1100);
  });

  it("moves a point across the left seam when that is the shortest route", () => {
    expect(wrappedXNear(900, 100, 1000)).toBe(-100);
  });

  it("leaves points on the same side of the map unchanged", () => {
    expect(wrappedXNear(650, 400, 1000)).toBe(650);
  });
});

describe("wrappedPointNear", () => {
  it("preserves y while wrapping x", () => {
    expect(wrappedPointNear({ x: 900, y: 25 }, { x: 100, y: 80 }, 1000)).toEqual({
      x: -100,
      y: 25,
    });
  });
});

describe("nearestWorldCopyIndex", () => {
  it("identifies the prepared centre and neighbouring copies", () => {
    expect(nearestWorldCopyIndex(500, 500, 1000)).toBe(0);
    expect(nearestWorldCopyIndex(1500, 500, 1000)).toBe(1);
    expect(nearestWorldCopyIndex(-500, 500, 1000)).toBe(-1);
  });

  it("identifies the next unloaded copy after a long drag", () => {
    expect(nearestWorldCopyIndex(2050, 500, 1000)).toBe(2);
    expect(nearestWorldCopyIndex(-1050, 500, 1000)).toBe(-2);
  });
});
