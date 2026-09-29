import type { ViewBox } from "../InteractiveMap/dsvgParser";
import { formatCoord } from "../InteractiveMap/svgPrimitives";
import { flattenPath } from "./pathFlatten";

export const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";
export const HOVER_FILL = "rgba(255, 255, 255, 0.6)";
export const ACTIVE_STROKE = "#FFFFFF";
// The highlight overlay paints above the baked-in borders layer, so the stroke
// reads thicker than it did in the SVG map (where it sat below the borders).
// Keep it thinner to compensate.
export const ACTIVE_STROKE_WIDTH = 3;
const WRAPPED_STROKE_CLIP_ID = "wrappedHighlightStrokeClip";
// A stroke centred exactly on a map edge extends half its width into the visible
// board. Include a small anti-aliasing allowance so no pale fringe survives.
const WRAPPED_STROKE_GUTTER = ACTIVE_STROKE_WIDTH / 2 + 0.5;

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
  horizontalWrap?: boolean;
};

const wrappedSeamBridges = (d: string, viewBox: ViewBox): string => {
  const left = viewBox.minX;
  const right = viewBox.minX + viewBox.width;
  const tolerance = Math.max(0.1, viewBox.width * 0.0001);
  const commands: string[] = [];

  for (const ring of flattenPath(d)) {
    for (let index = 1; index < ring.length; index++) {
      const from = ring[index - 1];
      const to = ring[index];
      const fromLeft = Math.abs(from.x - left);
      const toLeft = Math.abs(to.x - left);
      const fromRight = Math.abs(from.x - right);
      const toRight = Math.abs(to.x - right);
      const touchesGutter =
        Math.min(fromLeft, toLeft, fromRight, toRight) <= WRAPPED_STROKE_GUTTER;
      if (!touchesGutter) continue;

      // Do not restore the nearly vertical closing edge that the SVG path needs
      // in order to fill a piece cut by the seam. All other segments that enter
      // the gutter are real province outlines and should meet their continuation
      // on the neighbouring map copy.
      const seamParallel =
        Math.abs(from.x - to.x) <= tolerance &&
        ((fromLeft <= WRAPPED_STROKE_GUTTER &&
          toLeft <= WRAPPED_STROKE_GUTTER) ||
          (fromRight <= WRAPPED_STROKE_GUTTER &&
            toRight <= WRAPPED_STROKE_GUTTER));
      if (seamParallel) continue;

      commands.push(
        `M${formatCoord(from.x)} ${formatCoord(from.y)}L${formatCoord(to.x)} ${formatCoord(to.y)}`
      );
    }
  }

  if (commands.length === 0) return "";
  return (
    `<path d="${commands.join("")}" fill="none" stroke="${ACTIVE_STROKE}"` +
    ` stroke-width="${ACTIVE_STROKE_WIDTH}" stroke-linecap="round"` +
    ' stroke-linejoin="round" pointer-events="none"/>'
  );
};

const activePath = (
  d: string,
  fill: string,
  horizontalWrap: boolean,
  viewBox: ViewBox
): string => {
  const fillRule = ' fill-rule="evenodd" pointer-events="none"';
  if (!horizontalWrap) {
    return (
      `<path d="${d}" fill="${fill}" stroke="${ACTIVE_STROKE}"` +
      ` stroke-width="${ACTIVE_STROKE_WIDTH}"${fillRule}/>`
    );
  }

  // A province split across the left/right seam is encoded as closed SVG
  // subpaths. Filling those subpaths is correct, but stroking them also paints
  // their artificial closing edges. Paint the fill separately, then clip only
  // the outline away from the two horizontal map edges.
  return (
    `<path d="${d}" fill="${fill}" stroke="none"${fillRule}/>` +
    `<path d="${d}" fill="none" stroke="${ACTIVE_STROKE}"` +
    ` stroke-width="${ACTIVE_STROKE_WIDTH}" clip-path="url(#${WRAPPED_STROKE_CLIP_ID})"` +
    `${fillRule}/>` +
    wrappedSeamBridges(d, viewBox)
  );
};

const wrappedStrokeClip = (viewBox: ViewBox): string => {
  const { minX, minY, width, height } = viewBox;
  const x = minX + WRAPPED_STROKE_GUTTER;
  const y = minY - ACTIVE_STROKE_WIDTH;
  const clippedWidth = Math.max(0, width - WRAPPED_STROKE_GUTTER * 2);
  const clippedHeight = height + ACTIVE_STROKE_WIDTH * 2;
  return (
    `<defs><clipPath id="${WRAPPED_STROKE_CLIP_ID}" clipPathUnits="userSpaceOnUse">` +
    `<rect x="${x}" y="${y}" width="${clippedWidth}" height="${clippedHeight}"/>` +
    "</clipPath></defs>"
  );
};

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
    if (d) {
      layers.push(
        activePath(
          d,
          "url(#highlightedStripes)",
          input.horizontalWrap ?? false,
          input.viewBox
        )
      );
    }
  }

  if (
    input.hovered &&
    input.renderable.has(input.hovered) &&
    !input.selected.has(input.hovered)
  ) {
    const d = input.paths.get(input.hovered);
    if (d)
      layers.push(
        activePath(d, HOVER_FILL, input.horizontalWrap ?? false, input.viewBox)
      );
  }

  for (const id of input.selected) {
    const d = input.paths.get(id);
    if (d) {
      layers.push(
        activePath(
          d,
          SELECTED_FILL,
          input.horizontalWrap ?? false,
          input.viewBox
        )
      );
    }
  }

  const { minX, minY, width, height } = input.viewBox;
  return (
    `<svg xmlns="http://www.w3.org/2000/svg"` +
    ` viewBox="${minX} ${minY} ${width} ${height}">` +
    STRIPES_DEFS +
    (input.horizontalWrap ? wrappedStrokeClip(input.viewBox) : "") +
    layers.join("") +
    "</svg>"
  );
};
