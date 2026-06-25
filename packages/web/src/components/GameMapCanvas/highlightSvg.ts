import type { ViewBox } from "../InteractiveMap/dsvgParser";

export const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";
export const HOVER_FILL = "rgba(255, 255, 255, 0.6)";
export const ACTIVE_STROKE = "#FFFFFF";
// The highlight overlay paints above the baked-in borders layer, so the stroke
// reads thicker than it did in the SVG map (where it sat below the borders).
// Keep it thinner to compensate.
export const ACTIVE_STROKE_WIDTH = 3;

const STRIPES_DEFS =
  '<defs><pattern patternTransform="rotate(45)" height="8" width="8"' +
  ' patternUnits="userSpaceOnUse" id="highlightedStripes">' +
  '<line stroke-width="2" stroke-opacity="0.6" stroke="#FFFFFF"' +
  ' y2="8" x2="0" y1="0" x1="0"/></pattern></defs>';

export type HighlightInput = {
  paths: Map<string, string>;
  viewBox: ViewBox;
  selected: Set<string>;
  highlighted: Set<string>;
  renderable: Set<string>;
  hovered: string | null;
};

const activePath = (d: string, fill: string): string =>
  `<path d="${d}" fill="${fill}" stroke="${ACTIVE_STROKE}"` +
  ` stroke-width="${ACTIVE_STROKE_WIDTH}" fill-rule="evenodd"` +
  ' pointer-events="none"/>';

// Builds an SVG holding the exact province shapes for the currently active
// (highlighted / hovered / selected) provinces. The hit-test polygons stay
// invisible; this overlay is what the user actually sees highlight on, so it
// uses the full-resolution dSVG path data rather than the decimated rings.
// Paint order matches the SVG map: highlight stripes, then hover, then
// selection on top.
export const buildHighlightSvg = (input: HighlightInput): string => {
  const layers: string[] = [];

  for (const id of input.highlighted) {
    if (input.selected.has(id)) continue;
    const d = input.paths.get(id);
    if (d) layers.push(activePath(d, "url(#highlightedStripes)"));
  }

  if (
    input.hovered &&
    input.renderable.has(input.hovered) &&
    !input.selected.has(input.hovered)
  ) {
    const d = input.paths.get(input.hovered);
    if (d) layers.push(activePath(d, HOVER_FILL));
  }

  for (const id of input.selected) {
    const d = input.paths.get(id);
    if (d) layers.push(activePath(d, SELECTED_FILL));
  }

  const { minX, minY, width, height } = input.viewBox;
  return (
    `<svg xmlns="http://www.w3.org/2000/svg"` +
    ` viewBox="${minX} ${minY} ${width} ${height}">` +
    STRIPES_DEFS +
    layers.join("") +
    "</svg>"
  );
};
