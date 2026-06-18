import type { ViewBox } from "./dsvgParser";

export type Dimensions = {
  width: number;
  height: number;
};

export type TransformState = {
  scale: number;
  positionX: number;
  positionY: number;
};

// Converts RZPP's CSS transform of the transparent hit layer to an SVG viewBox for the visual layer.
export const transformToViewBox = (
  state: TransformState,
  container: Dimensions,
  mapViewBox: ViewBox
): ViewBox => {
  const scale = state.scale;
  return {
    minX: mapViewBox.minX - state.positionX / scale,
    minY: mapViewBox.minY - state.positionY / scale,
    width: container.width / scale,
    height: container.height / scale,
  };
};

export const viewBoxToString = (viewBox: ViewBox): string =>
  `${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`;

// Sets viewBox imperatively — bypasses React so per-frame gesture updates don't trigger re-renders.
export const applyViewBox = (
  svg: SVGSVGElement | null,
  viewBox: ViewBox
): void => {
  svg?.setAttribute("viewBox", viewBoxToString(viewBox));
};
