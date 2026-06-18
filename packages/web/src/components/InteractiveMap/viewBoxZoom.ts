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

// Converts react-zoom-pan-pinch's CSS transform of the (intrinsic-sized,
// transparent) hit layer into the visible window expressed as an SVG viewBox.
// The hit layer's content-local pixels map 1:1 to user units offset by the map
// viewBox origin, so the visible window is just the container rect projected
// back through the transform. Shared by every viewBox-driven map surface
// (InteractiveMapZoomWrapper, TutorialMap, ExpandableMapPreview).
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

// Sets the viewBox imperatively. The visible MapVisual layer owns its viewBox
// outside React so per-frame gesture updates don't trigger re-renders and React
// never clobbers the live value.
export const applyViewBox = (
  svg: SVGSVGElement | null,
  viewBox: ViewBox
): void => {
  svg?.setAttribute("viewBox", viewBoxToString(viewBox));
};
