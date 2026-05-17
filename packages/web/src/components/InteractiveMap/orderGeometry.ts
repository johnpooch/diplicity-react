import type { Point } from "./dsvgParser";

export const ROUTE_TENSION = 0.6;
export const MOVE_CURVE_OFFSET = 20;
export const SUPPORT_STAGGER_DISTANCE = 4.375;

export const euclidean = (a: Point, b: Point): number =>
  Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);

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

const permutations = <T>(items: T[]): T[][] => {
  if (items.length <= 1) {
    return [items];
  }
  return items.flatMap((item, i) =>
    permutations([...items.slice(0, i), ...items.slice(i + 1)]).map((rest) => [
      item,
      ...rest,
    ])
  );
};

export const shortestWaypointOrder = <T>(
  items: T[],
  pointOf: (item: T) => Point,
  source: Point,
  destination: Point
): T[] => {
  if (items.length <= 1) {
    return items;
  }
  const pathLength = (order: T[]): number => {
    let total = euclidean(source, pointOf(order[0]));
    for (let i = 0; i < order.length - 1; i++) {
      total += euclidean(pointOf(order[i]), pointOf(order[i + 1]));
    }
    return total + euclidean(pointOf(order[order.length - 1]), destination);
  };
  return permutations(items).reduce((best, order) =>
    pathLength(order) < pathLength(best) ? order : best
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
  fleets: ConvoyFleet[]
): ConvoyRoute => {
  const ordered = shortestWaypointOrder(
    fleets,
    (fleet) => fleet.point,
    source,
    destination
  );
  const waypoints = [source, ...ordered.map((fleet) => fleet.point), destination];
  const attachments = new Map<string, Point>();
  ordered.forEach((fleet, index) => {
    attachments.set(fleet.id, bSplineAttachmentPoint(waypoints, index + 1));
  });
  return { waypoints, attachments };
};
