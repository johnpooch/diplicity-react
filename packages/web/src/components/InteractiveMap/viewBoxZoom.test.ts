import { describe, it, expect, vi } from "vitest";
import { transformToViewBox, viewBoxToString, applyViewBox } from "./viewBoxZoom";
import type { ViewBox } from "./dsvgParser";

describe("transformToViewBox", () => {
  const mapViewBox: ViewBox = { minX: 0, minY: 0, width: 1000, height: 800 };
  const container = { width: 500, height: 400 };

  it("at scale 1 with no pan, returns container-sized window at map origin", () => {
    expect(
      transformToViewBox({ scale: 1, positionX: 0, positionY: 0 }, container, mapViewBox)
    ).toEqual({ minX: 0, minY: 0, width: 500, height: 400 });
  });

  it("scaling up halves the viewBox dimensions", () => {
    expect(
      transformToViewBox({ scale: 2, positionX: 0, positionY: 0 }, container, mapViewBox)
    ).toEqual({ minX: 0, minY: 0, width: 250, height: 200 });
  });

  it("panning right shifts minX left", () => {
    expect(
      transformToViewBox({ scale: 1, positionX: 100, positionY: 0 }, container, mapViewBox)
    ).toEqual({ minX: -100, minY: 0, width: 500, height: 400 });
  });

  it("panning down shifts minY up", () => {
    expect(
      transformToViewBox({ scale: 1, positionX: 0, positionY: 50 }, container, mapViewBox)
    ).toEqual({ minX: 0, minY: -50, width: 500, height: 400 });
  });

  it("combines scale and pan correctly", () => {
    expect(
      transformToViewBox({ scale: 2, positionX: 100, positionY: 80 }, container, mapViewBox)
    ).toEqual({ minX: -50, minY: -40, width: 250, height: 200 });
  });

  it("respects a non-zero mapViewBox origin", () => {
    const offsetViewBox: ViewBox = { minX: 100, minY: 50, width: 1000, height: 800 };
    expect(
      transformToViewBox({ scale: 1, positionX: 0, positionY: 0 }, container, offsetViewBox)
    ).toEqual({ minX: 100, minY: 50, width: 500, height: 400 });
  });
});

describe("viewBoxToString", () => {
  it("formats viewBox as space-separated values", () => {
    expect(viewBoxToString({ minX: 0, minY: 0, width: 1000, height: 800 })).toBe("0 0 1000 800");
  });

  it("handles fractional and negative values", () => {
    expect(viewBoxToString({ minX: -50.5, minY: -40, width: 250, height: 200 })).toBe(
      "-50.5 -40 250 200"
    );
  });
});

describe("applyViewBox", () => {
  it("sets the viewBox attribute on the SVG element", () => {
    const svg = { setAttribute: vi.fn() } as unknown as SVGSVGElement;
    applyViewBox(svg, { minX: 0, minY: 0, width: 1000, height: 800 });
    expect(svg.setAttribute).toHaveBeenCalledWith("viewBox", "0 0 1000 800");
  });

  it("does nothing when svg is null", () => {
    expect(() => applyViewBox(null, { minX: 0, minY: 0, width: 100, height: 100 })).not.toThrow();
  });
});
