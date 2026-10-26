import { stripRedundantNamespace, type ViewBox } from "../InteractiveMap/dsvgParser";
import { DiplicityMap, type RenderState } from "../InteractiveMap/mapRenderer";

export type SplitSvg = {
  base: string;
  labels: string;
  overlay: string;
};

const SVG_NS = "http://www.w3.org/2000/svg";
const OVERLAY_LAYER_IDS = ['<g id="units">', '<g id="orders">'];
const NAMES_LAYER_OPEN = '<g id="province-names">';
const NAMES_LAYER_NEXT = '<g id="borders">';

const viewBoxAttr = (viewBox: ViewBox): string =>
  `${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`;

const isTextLabel = (element: Element): boolean =>
  element.tagName.toLowerCase() === "text" ||
  element.getElementsByTagName("text").length > 0;

const partitionNames = (markup: string): { raster: string; labels: string } => {
  const doc = new DOMParser().parseFromString(
    `<svg xmlns="${SVG_NS}">${markup}</svg>`,
    "image/svg+xml"
  );
  let raster = "";
  let labels = "";
  for (const child of Array.from(doc.documentElement.children)) {
    if (isTextLabel(child)) {
      labels += child.outerHTML;
    } else {
      raster += child.outerHTML;
    }
  }
  return {
    raster: stripRedundantNamespace(raster),
    labels: stripRedundantNamespace(labels),
  };
};

// Splits a fully rendered map SVG into a static base (everything except the
// text labels and the units and orders layers, which always come last), a
// labels layer holding the province name text, and a light overlay holding
// just the units and orders. The base is rasterised once; the labels and the
// overlay are vector layers, and only the overlay repaints on interaction.
export const splitRenderedSvg = (svg: string, viewBox: ViewBox): SplitSvg => {
  const rootTag = svg.slice(0, svg.indexOf(">") + 1);
  const closeIndex = svg.lastIndexOf("</svg>");
  const overlayStarts = OVERLAY_LAYER_IDS.map((id) => svg.indexOf(id)).filter(
    (index) => index >= 0
  );
  const cut = overlayStarts.length > 0 ? Math.min(...overlayStarts) : closeIndex;

  let staticLayers = svg.slice(0, cut).trimEnd();
  let labelsInner = "";
  const namesStart = staticLayers.indexOf(NAMES_LAYER_OPEN);
  const namesNext = staticLayers.indexOf(NAMES_LAYER_NEXT, namesStart);
  if (namesStart >= 0 && namesNext >= 0) {
    const namesLayer = staticLayers.slice(namesStart, namesNext).trimEnd();
    const { raster, labels } = partitionNames(
      namesLayer.slice(NAMES_LAYER_OPEN.length, -"</g>".length)
    );
    labelsInner = labels;
    staticLayers =
      staticLayers.slice(0, namesStart) +
      `${NAMES_LAYER_OPEN}${raster}</g>\n` +
      staticLayers.slice(namesNext);
  }

  const base = staticLayers + "\n" + svg.slice(closeIndex);
  const labels = `${rootTag}${labelsInner}</svg>`;
  const overlayInner = svg.slice(cut, closeIndex).trim();
  const overlay = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBoxAttr(
    viewBox
  )}">${overlayInner}</svg>`;

  return { base, labels, overlay };
};

// Renders the board with the given render state but never paints selection or
// highlight into the base (those are interactive, drawn by the hit-test layer),
// then splits it into base, labels and overlay SVG strings.
export const renderSplitSvg = (
  renderer: DiplicityMap,
  state: RenderState,
  viewBox: ViewBox
): SplitSvg => {
  const svg = renderer.render({ ...state, selected: [], highlighted: [] });
  return splitRenderedSvg(svg, viewBox);
};
