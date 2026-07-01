import type { Point } from "../InteractiveMap/dsvgParser";

const perpendicularDistance = (p: Point, a: Point, b: Point): number => {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const lengthSquared = dx * dx + dy * dy;
  if (lengthSquared === 0) {
    return Math.hypot(p.x - a.x, p.y - a.y);
  }
  const t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / lengthSquared;
  const projX = a.x + t * dx;
  const projY = a.y + t * dy;
  return Math.hypot(p.x - projX, p.y - projY);
};

// Ramer–Douglas–Peucker line simplification. Returns a subset of the input
// points whose deviation from the original never exceeds `tolerance`. Used to
// turn the dense province rings into cheap hit-test polygons.
export const decimate = (points: Point[], tolerance: number): Point[] => {
  if (points.length <= 2) {
    return [...points];
  }

  let maxDistance = 0;
  let index = 0;
  const last = points.length - 1;
  for (let i = 1; i < last; i++) {
    const distance = perpendicularDistance(points[i], points[0], points[last]);
    if (distance > maxDistance) {
      maxDistance = distance;
      index = i;
    }
  }

  if (maxDistance <= tolerance) {
    return [points[0], points[last]];
  }

  const left = decimate(points.slice(0, index + 1), tolerance);
  const right = decimate(points.slice(index), tolerance);
  return [...left.slice(0, -1), ...right];
};
