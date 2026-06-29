import { describe, it, expect } from "vitest";
import { focusBounds } from "./focusBounds";

describe("focusBounds", () => {
  it("returns null when none of the ids have a known path", () => {
    const paths = new Map([["abc", "M0 0 L10 0 L10 10 Z"]]);
    expect(focusBounds(paths, ["xyz"], 1)).toBeNull();
  });

  it("returns the tight bounding box with padding 1", () => {
    const paths = new Map([["abc", "M0 0 L10 0 L10 20 L0 20 Z"]]);
    expect(focusBounds(paths, ["abc"], 1)).toEqual({
      minX: 0,
      minY: 0,
      maxX: 10,
      maxY: 20,
    });
  });

  it("scales the box about its centre by the padding factor", () => {
    const paths = new Map([["abc", "M0 0 L10 0 L10 10 L0 10 Z"]]);
    expect(focusBounds(paths, ["abc"], 1.4)).toEqual({
      minX: -2,
      minY: -2,
      maxX: 12,
      maxY: 12,
    });
  });

  it("spans the union of multiple provinces, ignoring unknown ids", () => {
    const paths = new Map([
      ["a", "M0 0 L10 0 L10 10 L0 10 Z"],
      ["b", "M20 20 L30 20 L30 30 L20 30 Z"],
    ]);
    expect(focusBounds(paths, ["a", "b", "missing"], 1)).toEqual({
      minX: 0,
      minY: 0,
      maxX: 30,
      maxY: 30,
    });
  });
});
