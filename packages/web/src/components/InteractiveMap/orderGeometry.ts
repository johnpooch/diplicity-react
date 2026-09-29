import type { Point } from "./dsvgParser";
import { wrappedPointNear } from "./mapWrap";

export const ROUTE_TENSION = 0.6;
export const MOVE_CURVE_OFFSET = 20;
export const SUPPORT_STAGGER_DISTANCE = 4.375;

export const euclidean = (a: Point, b: Point): number =>
  Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);

export const wrappedEuclidean = (
  a: Point,
  b: Point,
  width?: number
): number => euclidean(a, wrappedPointNear(b, a, width));

export const closestPointOnLine = (p: Point, a: Point, b: Point): Point => {
  const lineX = b.x - a.x;
  const lineY = b.y - a.y;
  const pointX = p.x - a.x;
  const pointY = p.y - a.y;
  const lengthSquared = lineX * lineX + lineY * lineY;
  const t = Math.max(
    0.1,
    Math.min(0.9, (pointX * lineX + pointY * lineY) / lengthSquared)
  );
  return { x: a.x + t * lineX, y: a.y + t * lineY };
};

export const bSplineAttachmentPoint = (points: Point[], i: number): Point => {
  const previous = points[i - 1];
  const current = points[i];
  const next = points[i + 1];
  const mid0 = {
    x: (previous.x + current.x) / 2,
    y: (previous.y + current.y) / 2,
  };
  const mid1 = { x: (current.x + next.x) / 2, y: (current.y + next.y) / 2 };
  const midOfMids = { x: (mid0.x + mid1.x) / 2, y: (mid0.y + mid1.y) / 2 };
  const control = {
    x: midOfMids.x + ROUTE_TENSION * (current.x - midOfMids.x),
    y: midOfMids.y + ROUTE_TENSION * (current.y - midOfMids.y),
  };
  return {
    x: 0.25 * mid0.x + 0.5 * control.x + 0.25 * mid1.x,
    y: 0.25 * mid0.y + 0.5 * control.y + 0.25 * mid1.y,
  };
};

// Exact routing is cheap at the convoy sizes used by normal games. Above this
// threshold, exponential work is unnecessary for a visual aid, so use a
// deterministic insertion heuristic instead of risking a frozen browser.
export const EXACT_WAYPOINT_LIMIT = 12;

const exactWaypointOrder = <T>(
  items: T[],
  pointOf: (item: T) => Point,
  source: Point,
  destination: Point,
  horizontalWrapWidth?: number
): T[] => {
  const count = items.length;
  const stateCount = 1 << count;
  const costs = new Float64Array(stateCount * count);
  costs.fill(Number.POSITIVE_INFINITY);
  const previous = new Int16Array(stateCount * count);
  previous.fill(-1);
  const indexOf = (mask: number, last: number): number => mask * count + last;

  for (let i = 0; i < count; i++) {
    costs[indexOf(1 << i, i)] = wrappedEuclidean(
      source,
      pointOf(items[i]),
      horizontalWrapWidth
    );
  }

  for (let mask = 1; mask < stateCount; mask++) {
    for (let last = 0; last < count; last++) {
      if ((mask & (1 << last)) === 0) continue;
      const cost = costs[indexOf(mask, last)];
      if (!Number.isFinite(cost)) continue;

      for (let next = 0; next < count; next++) {
        if ((mask & (1 << next)) !== 0) continue;
        const nextMask = mask | (1 << next);
        const nextIndex = indexOf(nextMask, next);
        const nextCost =
          cost +
          wrappedEuclidean(
            pointOf(items[last]),
            pointOf(items[next]),
            horizontalWrapWidth
          );
        if (nextCost < costs[nextIndex]) {
          costs[nextIndex] = nextCost;
          previous[nextIndex] = last;
        }
      }
    }
  }

  const fullMask = stateCount - 1;
  let bestLast = 0;
  let bestCost = Number.POSITIVE_INFINITY;
  for (let last = 0; last < count; last++) {
    const total =
      costs[indexOf(fullMask, last)] +
      wrappedEuclidean(pointOf(items[last]), destination, horizontalWrapWidth);
    if (total < bestCost) {
      bestCost = total;
      bestLast = last;
    }
  }

  const result = new Array<T>(count);
  let mask = fullMask;
  let last = bestLast;
  for (let position = count - 1; position >= 0; position--) {
    result[position] = items[last];
    const prior = previous[indexOf(mask, last)];
    mask ^= 1 << last;
    last = prior;
  }
  return result;
};

const approximateWaypointOrder = <T>(
  items: T[],
  pointOf: (item: T) => Point,
  source: Point,
  destination: Point,
  horizontalWrapWidth?: number
): T[] => {
  const remaining = [...items];
  const result: T[] = [];

  while (remaining.length > 0) {
    let bestItemIndex = 0;
    let bestPosition = 0;
    let bestIncrease = Number.POSITIVE_INFINITY;

    for (let itemIndex = 0; itemIndex < remaining.length; itemIndex++) {
      const point = pointOf(remaining[itemIndex]);
      for (let position = 0; position <= result.length; position++) {
        const before = position === 0 ? source : pointOf(result[position - 1]);
        const after =
          position === result.length ? destination : pointOf(result[position]);
        const increase =
          wrappedEuclidean(before, point, horizontalWrapWidth) +
          wrappedEuclidean(point, after, horizontalWrapWidth) -
          wrappedEuclidean(before, after, horizontalWrapWidth);
        if (increase < bestIncrease) {
          bestIncrease = increase;
          bestItemIndex = itemIndex;
          bestPosition = position;
        }
      }
    }

    const [item] = remaining.splice(bestItemIndex, 1);
    result.splice(bestPosition, 0, item);
  }

  return result;
};

export const shortestWaypointOrder = <T>(
  items: T[],
  pointOf: (item: T) => Point,
  source: Point,
  destination: Point,
  horizontalWrapWidth?: number
): T[] => {
  if (items.length <= 1) {
    return items;
  }
  return items.length <= EXACT_WAYPOINT_LIMIT
    ? exactWaypointOrder(
        items,
        pointOf,
        source,
        destination,
        horizontalWrapWidth
      )
    : approximateWaypointOrder(
        items,
        pointOf,
        source,
        destination,
        horizontalWrapWidth
      );
};

export const headToHeadControlPoint = (p1: Point, p2: Point): Point => {
  const midX = (p1.x + p2.x) / 2;
  const midY = (p1.y + p2.y) / 2;
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const length = Math.sqrt(dx * dx + dy * dy);
  return {
    x: midX + (-dy / length) * MOVE_CURVE_OFFSET,
    y: midY + (dx / length) * MOVE_CURVE_OFFSET,
  };
};

export const staggeredSupportEnd = (
  aux: Point,
  target: Point,
  staggerIndex: number,
  moveControlPoint?: Point
): Point => {
  const staggerDistance = (staggerIndex + 1) * SUPPORT_STAGGER_DISTANCE;
  if (moveControlPoint) {
    const dx = target.x - moveControlPoint.x;
    const dy = target.y - moveControlPoint.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    return {
      x: target.x - (dx / length) * staggerDistance,
      y: target.y - (dy / length) * staggerDistance,
    };
  }
  const dx = aux.x - target.x;
  const dy = aux.y - target.y;
  const length = Math.sqrt(dx * dx + dy * dy);
  return {
    x: target.x + (dx / length) * staggerDistance,
    y: target.y + (dy / length) * staggerDistance,
  };
};

export type ConvoyFleet = { id: string; point: Point };

export type ConvoyRoute = {
  waypoints: Point[];
  attachments: Map<string, Point>;
};

export const buildConvoyRoute = (
  source: Point,
  destination: Point,
  fleets: ConvoyFleet[],
  horizontalWrapWidth?: number
): ConvoyRoute => {
  const ordered = shortestWaypointOrder(
    fleets,
    (fleet) => fleet.point,
    source,
    destination,
    horizontalWrapWidth
  );
  const canonicalWaypoints = [
    source,
    ...ordered.map((fleet) => fleet.point),
    destination,
  ];
  const waypoints = canonicalWaypoints.reduce<Point[]>((result, point) => {
    const previous = result[result.length - 1];
    result.push(previous ? wrappedPointNear(point, previous, horizontalWrapWidth) : point);
    return result;
  }, []);
  const attachments = new Map<string, Point>();
  ordered.forEach((fleet, index) => {
    attachments.set(fleet.id, bSplineAttachmentPoint(waypoints, index + 1));
  });
  return { waypoints, attachments };
};
