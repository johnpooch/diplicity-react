import type { LatLngExpression, LatLngBoundsLiteral } from "leaflet";
import type { Point, ViewBox } from "../InteractiveMap/dsvgParser";

// Leaflet's CRS.Simple projects a LatLng to the pixel point (lng, -lat). To make
// an SVG coordinate (x, y) with y pointing down land at the matching pixel we map
// it to the LatLng [-y, x]. Every coordinate handed to Leaflet goes through here.
export const toLatLng = (p: Point): LatLngExpression => [-p.y, p.x];

// The image/overlay bounds span the dSVG viewBox: top-left at the origin,
// bottom-right at (width, height) in pixel space → [-height, width] in LatLng.
export const viewBoxBounds = (viewBox: ViewBox): LatLngBoundsLiteral => [
  [0, 0],
  [-viewBox.height, viewBox.width],
];
