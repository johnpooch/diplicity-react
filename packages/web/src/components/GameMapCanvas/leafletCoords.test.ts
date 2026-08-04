import { describe, expect, it } from "vitest";
import { shiftedViewBoxBounds, viewBoxBounds } from "./leafletCoords";

const viewBox = {
  minX: 20,
  minY: 30,
  width: 600,
  height: 400,
};

describe("viewBoxBounds", () => {
  it("preserves a non-zero dSVG origin", () => {
    expect(viewBoxBounds(viewBox)).toEqual([
      [-30, 20],
      [-430, 620],
    ]);
  });

  it("shifts only the horizontal bounds for a repeated world", () => {
    expect(shiftedViewBoxBounds(viewBox, -600)).toEqual([
      [-30, -580],
      [-430, 20],
    ]);
  });
});
