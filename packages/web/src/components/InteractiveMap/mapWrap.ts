import type { Point } from "./dsvgParser";

export const WORLD_COPY_INDEXES = [0, -1, 1] as const;

export const wrappedXNear = (
  x: number,
  referenceX: number,
  width: number
): number => {
  if (width <= 0) return x;
  return x + Math.round((referenceX - x) / width) * width;
};

export const wrappedPointNear = (
  point: Point,
  reference: Point,
  width: number | undefined
): Point =>
  width
    ? { x: wrappedXNear(point.x, reference.x, width), y: point.y }
    : point;

export const nearestWorldCopyIndex = (
  x: number,
  canonicalCenterX: number,
  width: number
): number => (width > 0 ? Math.round((x - canonicalCenterX) / width) : 0);
