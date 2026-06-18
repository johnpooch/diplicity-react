export const HOVER_STROKE_WIDTH = 5;
export const HOVER_STROKE_COLOR = "white";
export const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

export const stripSvgWrapper = (svg: string): string => {
  const openEnd = svg.indexOf(">");
  const closeStart = svg.lastIndexOf("</svg>");
  if (openEnd === -1 || closeStart === -1) {
    return svg;
  }
  return svg.slice(openEnd + 1, closeStart).trim();
};

const ABOVE_HOVER_LAYER_IDS = [
  "supply-center-markers",
  "province-names",
  "borders",
  "foreground",
  "units",
  "orders",
];

export const splitAfterProvinceFills = (
  inner: string
): { below: string; above: string } => {
  const candidates = ABOVE_HOVER_LAYER_IDS.map((id) =>
    inner.indexOf(`<g id="${id}">`)
  ).filter((index) => index !== -1);
  if (candidates.length === 0) {
    return { below: inner, above: "" };
  }
  const splitIndex = Math.min(...candidates);
  return {
    below: inner.slice(0, splitIndex),
    above: inner.slice(splitIndex),
  };
};
