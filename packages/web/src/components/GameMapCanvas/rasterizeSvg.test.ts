import { describe, it, expect } from "vitest";
import { computeRasterDimensions, injectSvgDimensions } from "./rasterizeSvg";

describe("injectSvgDimensions", () => {
  it("stamps width and height onto the root svg tag", () => {
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><g/></svg>';
    const sized = injectSvgDimensions(svg, 100, 50);
    expect(sized).toBe(
      '<svg width="100" height="50" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><g/></svg>'
    );
  });

  it("preserves the existing viewBox so aspect ratio is unchanged", () => {
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1234.5 987.25"></svg>';
    const sized = injectSvgDimensions(svg, 1234.5, 987.25);
    expect(sized).toContain('viewBox="0 0 1234.5 987.25"');
    expect(sized).toContain('width="1234.5"');
    expect(sized).toContain('height="987.25"');
  });
});

describe("computeRasterDimensions", () => {
  it("leaves dimensions unchanged when already within the pixel budget", () => {
    const dimensions = computeRasterDimensions(1000, 1000, 4_000_000);
    expect(dimensions).toEqual({ width: 1000, height: 1000 });
  });

  it("scales down large viewboxes to fit the pixel budget", () => {
    const dimensions = computeRasterDimensions(4000, 4000, 4_000_000);
    expect(dimensions.width * dimensions.height).toBeCloseTo(4_000_000, 0);
    expect(dimensions.width).toBeCloseTo(2000, 5);
    expect(dimensions.height).toBeCloseTo(2000, 5);
  });

  it("preserves aspect ratio for non-square viewboxes", () => {
    const dimensions = computeRasterDimensions(8000, 2000, 4_000_000);
    expect(dimensions.width / dimensions.height).toBeCloseTo(4, 5);
    expect(dimensions.width * dimensions.height).toBeLessThanOrEqual(4_000_000);
  });
});
