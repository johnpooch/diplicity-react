import { describe, it, expect } from "vitest";
import { buildHighlightSvg, SELECTED_FILL, HOVER_FILL } from "./highlightSvg";
import type { ViewBox } from "../InteractiveMap/dsvgParser";

const viewBox: ViewBox = { minX: 0, minY: 0, width: 100, height: 80 };

const paths = new Map<string, string>([
  ["lon", "M0 0 L10 0 L10 10 Z"],
  ["wal", "M20 0 L30 0 L30 10 Z"],
  ["nth", "M40 0 L50 0 L50 10 Z"],
]);

const base = {
  paths,
  viewBox,
  selected: new Set<string>(),
  highlighted: new Set<string>(),
  renderable: new Set<string>(["lon", "wal", "nth"]),
  hovered: null as string | null,
};

describe("buildHighlightSvg", () => {
  it("uses the full-resolution province path for the selected province", () => {
    const svg = buildHighlightSvg({ ...base, selected: new Set(["lon"]) });
    expect(svg).toContain('d="M0 0 L10 0 L10 10 Z"');
    expect(svg).toContain(SELECTED_FILL);
  });

  it("renders the exact shape for the hovered renderable province", () => {
    const svg = buildHighlightSvg({ ...base, hovered: "wal" });
    expect(svg).toContain('d="M20 0 L30 0 L30 10 Z"');
    expect(svg).toContain(HOVER_FILL);
  });

  it("does not highlight a hovered province that is not renderable", () => {
    const svg = buildHighlightSvg({
      ...base,
      hovered: "wal",
      renderable: new Set(["lon"]),
    });
    expect(svg).not.toContain('d="M20 0 L30 0 L30 10 Z"');
  });

  it("draws highlighted provinces with stripes but not the selected one", () => {
    const svg = buildHighlightSvg({
      ...base,
      selected: new Set(["lon"]),
      highlighted: new Set(["lon", "nth"]),
    });
    expect(svg).toContain("url(#highlightedStripes)");
    expect(svg).toContain('d="M40 0 L50 0 L50 10 Z"');
    expect(svg).toContain('d="M0 0 L10 0 L10 10 Z"');
    expect(svg.match(/url\(#highlightedStripes\)/g)?.length).toBe(1);
  });

  it("emits a viewBox matching the parsed dSVG", () => {
    const svg = buildHighlightSvg(base);
    expect(svg).toContain('viewBox="0 0 100 80"');
  });

  it("skips provinces with no known path", () => {
    const svg = buildHighlightSvg({ ...base, selected: new Set(["unknown"]) });
    expect(svg).not.toContain("<path");
  });
});
