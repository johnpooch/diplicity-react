// Helper function to compute the projection of point (x1, y1) onto the line (x2, y2) -> (x3, y3)
const getClosestPointOnLine = (
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  x3: number,
  y3: number
) => {
  // Line vector (x2, y2) -> (x3, y3)
  const lineVecX = x3 - x2;
  const lineVecY = y3 - y2;

  // Point vector (x2, y2) -> (x1, y1)
  const pointVecX = x1 - x2;
  const pointVecY = y1 - y2;

  // Project point onto the line segment, clamped to [0, 1]
  const lineLengthSquared = lineVecX * lineVecX + lineVecY * lineVecY;
  const t = Math.max(
    0.1,
    Math.min(
      0.9,
      (pointVecX * lineVecX + pointVecY * lineVecY) / lineLengthSquared
    )
  );

  // Closest point on the segment
  const closestX = x2 + t * lineVecX;
  const closestY = y2 + t * lineVecY;

  return { x: closestX, y: closestY };
};

// Closest point on a multi-segment polyline to point (px, py).
// Each segment is clamped to [0, 1] independently.
const getClosestPointOnPolyline = (
  px: number,
  py: number,
  points: { x: number; y: number }[]
) => {
  let bestDistSq = Infinity;
  let bestPoint = points[0];

  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const lenSq = dx * dx + dy * dy;
    const t =
      lenSq === 0
        ? 0
        : Math.max(0, Math.min(1, ((px - p1.x) * dx + (py - p1.y) * dy) / lenSq));
    const cx = p1.x + t * dx;
    const cy = p1.y + t * dy;
    const distSq = (cx - px) ** 2 + (cy - py) ** 2;
    if (distSq < bestDistSq) {
      bestDistSq = distSq;
      bestPoint = { x: cx, y: cy };
    }
  }
  return bestPoint;
};

type Point = { x: number; y: number };

// Must match ROUTE_TENSION in move-via-convoy.tsx — controls how far the
// B-spline deviates toward each intermediate fleet waypoint.
export const ROUTE_TENSION = 0.6;

// For fleet at index `i` in the full waypoints array [src, f1, …, fn, dst],
// returns the point on the rendered B-spline that is closest to that fleet.
// This is the t=0.5 point on the fleet's quadratic bezier segment, which is
// where the curve reaches its closest approach to the (tensioned) control point.
export const bSplineAttachmentPoint = (pts: Point[], i: number): Point => {
  const pPrev = pts[i - 1];
  const p = pts[i];
  const pNext = pts[i + 1];
  const mid0 = { x: (pPrev.x + p.x) / 2, y: (pPrev.y + p.y) / 2 };
  const mid1 = { x: (p.x + pNext.x) / 2, y: (p.y + pNext.y) / 2 };
  const midOfMids = { x: (mid0.x + mid1.x) / 2, y: (mid0.y + mid1.y) / 2 };
  const ctrl = {
    x: midOfMids.x + ROUTE_TENSION * (p.x - midOfMids.x),
    y: midOfMids.y + ROUTE_TENSION * (p.y - midOfMids.y),
  };
  // Quadratic bezier at t=0.5
  return {
    x: 0.25 * mid0.x + 0.5 * ctrl.x + 0.25 * mid1.x,
    y: 0.25 * mid0.y + 0.5 * ctrl.y + 0.25 * mid1.y,
  };
};

const euclidean = (a: Point, b: Point) =>
  Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);

const permutations = <T>(arr: T[]): T[][] => {
  if (arr.length <= 1) return [arr];
  return arr.flatMap((item, i) =>
    permutations([...arr.slice(0, i), ...arr.slice(i + 1)]).map(rest => [
      item,
      ...rest,
    ])
  );
};

// Returns the ordering of `waypoints` that minimises total path length
// from `src` through all waypoints to `dst`.  Exhaustive for small N (≤ 8).
const shortestWaypointOrder = (
  waypoints: Point[],
  src: Point,
  dst: Point
): Point[] => {
  if (waypoints.length <= 1) return waypoints;

  const pathLen = (perm: Point[]) => {
    let d = euclidean(src, perm[0]);
    for (let i = 0; i < perm.length - 1; i++) d += euclidean(perm[i], perm[i + 1]);
    d += euclidean(perm[perm.length - 1], dst);
    return d;
  };

  return permutations(waypoints).reduce((best, perm) =>
    pathLen(perm) < pathLen(best) ? perm : best
  );
};

export { getClosestPointOnLine, getClosestPointOnPolyline, shortestWaypointOrder };
