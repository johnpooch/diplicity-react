import { describe, it, expect } from "vitest";
import { injectSvgDimensions } from "./rasterizeSvg";

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
