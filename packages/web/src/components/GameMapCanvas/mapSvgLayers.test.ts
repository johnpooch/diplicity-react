import { describe, it, expect } from "vitest";
import { splitRenderedSvg } from "./mapSvgLayers";
import type { ViewBox } from "../InteractiveMap/dsvgParser";

const viewBox: ViewBox = { minX: 0, minY: 0, width: 100, height: 50 };

const SAMPLE = [
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">',
  '<g id="background"><rect/></g>',
  '<g id="province-fills"><path/></g>',
  '<g id="units"><g><circle/></g></g>',
  '<g id="orders"><g><path/></g></g>',
  "</svg>",
].join("\n");

describe("splitRenderedSvg", () => {
  it("keeps the static layers in the base and removes units and orders", () => {
    const { base } = splitRenderedSvg(SAMPLE, viewBox);
    expect(base).toContain('id="background"');
    expect(base).toContain('id="province-fills"');
    expect(base).not.toContain('id="units"');
    expect(base).not.toContain('id="orders"');
    expect(base.endsWith("</svg>")).toBe(true);
  });

  it("collects only the units and orders layers into the overlay", () => {
    const { overlay } = splitRenderedSvg(SAMPLE, viewBox);
    expect(overlay).toContain('id="units"');
    expect(overlay).toContain('id="orders"');
    expect(overlay).not.toContain('id="background"');
    expect(overlay).toContain('viewBox="0 0 100 50"');
  });

  it("yields an empty overlay body when there are no units or orders", () => {
    const board = [
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">',
      '<g id="background"><rect/></g>',
      "</svg>",
    ].join("\n");
    const { base, overlay } = splitRenderedSvg(board, viewBox);
    expect(base).toContain('id="background"');
    expect(overlay).toBe(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"></svg>'
    );
  });
});
