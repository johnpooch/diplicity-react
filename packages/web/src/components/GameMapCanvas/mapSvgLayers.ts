import type { ViewBox } from "../InteractiveMap/dsvgParser";
import { DiplicityMap, type RenderState } from "../InteractiveMap/mapRenderer";

export type SplitSvg = {
  base: string;
  overlay: string;
};

const OVERLAY_LAYER_IDS = ['<g id="units">', '<g id="orders">'];

const viewBoxAttr = (viewBox: ViewBox): string =>
  `${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`;

// Splits a fully rendered map SVG into a static base (everything except the
// units and orders layers, which always come last) and a light overlay holding
// just those two layers. The base is rasterised once; the overlay repaints on
// interaction.
export const splitRenderedSvg = (svg: string, viewBox: ViewBox): SplitSvg => {
  const closeIndex = svg.lastIndexOf("</svg>");
  const overlayStarts = OVERLAY_LAYER_IDS.map((id) => svg.indexOf(id)).filter(
    (index) => index >= 0
  );
  const cut = overlayStarts.length > 0 ? Math.min(...overlayStarts) : closeIndex;

  const base = svg.slice(0, cut).trimEnd() + "\n" + svg.slice(closeIndex);
  const overlayInner = svg.slice(cut, closeIndex).trim();
  const overlay = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBoxAttr(
    viewBox
  )}">${overlayInner}</svg>`;

  return { base, overlay };
};

// Renders the board with the given render state but never paints selection or
// highlight into the base (those are interactive, drawn by the hit-test layer),
// then splits it into base + overlay SVG strings.
export const renderSplitSvg = (
  renderer: DiplicityMap,
  state: RenderState,
  viewBox: ViewBox
): SplitSvg => {
  const svg = renderer.render({ ...state, selected: [], highlighted: [] });
  return splitRenderedSvg(svg, viewBox);
};
