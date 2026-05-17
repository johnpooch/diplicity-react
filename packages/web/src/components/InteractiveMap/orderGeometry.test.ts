import { describe, test, expect } from "vitest";
import {
  euclidean,
  closestPointOnLine,
  bSplineAttachmentPoint,
  shortestWaypointOrder,
  headToHeadControlPoint,
  staggeredSupportEnd,
  buildConvoyRoute,
  MOVE_CURVE_OFFSET,
} from "./orderGeometry";

describe("euclidean", () => {
  test("measures the distance between two points", () => {
    expect(euclidean({ x: 0, y: 0 }, { x: 3, y: 4 })).toBe(5);
  });
});

describe("closestPointOnLine", () => {
  test("projects a point onto the segment", () => {
    expect(
      closestPointOnLine({ x: 5, y: 5 }, { x: 0, y: 0 }, { x: 10, y: 0 })
    ).toEqual({ x: 5, y: 0 });
  });

  test("clamps the projection to [0.1, 0.9] of the segment", () => {
    expect(
      closestPointOnLine({ x: -100, y: 0 }, { x: 0, y: 0 }, { x: 10, y: 0 })
    ).toEqual({ x: 1, y: 0 });
  });
});

describe("bSplineAttachmentPoint", () => {
  test("returns the point itself for collinear control points", () => {
    const points = [
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 20, y: 0 },
    ];
    expect(bSplineAttachmentPoint(points, 1)).toEqual({ x: 10, y: 0 });
  });

  test("eases toward the control point for a bend", () => {
    const points = [
      { x: 0, y: 0 },
      { x: 10, y: 10 },
      { x: 20, y: 0 },
    ];
    expect(bSplineAttachmentPoint(points, 1)).toEqual({ x: 10, y: 6.5 });
  });
});

describe("shortestWaypointOrder", () => {
  test("orders waypoints to minimise total path length", () => {
    const fleets = [
      { id: "far", point: { x: 20, y: 0 } },
      { id: "near", point: { x: 10, y: 0 } },
    ];
    const ordered = shortestWaypointOrder(
      fleets,
      (fleet) => fleet.point,
      { x: 0, y: 0 },
      { x: 30, y: 0 }
    );
    expect(ordered.map((fleet) => fleet.id)).toEqual(["near", "far"]);
  });

  test("returns a single item unchanged", () => {
    const items = [{ id: "only", point: { x: 5, y: 5 } }];
    expect(
      shortestWaypointOrder(items, (i) => i.point, { x: 0, y: 0 }, { x: 9, y: 9 })
    ).toBe(items);
  });
});

describe("headToHeadControlPoint", () => {
  test("offsets perpendicular to the line by the curve offset", () => {
    const control = headToHeadControlPoint({ x: 0, y: 0 }, { x: 20, y: 0 });
    expect(control).toEqual({ x: 10, y: MOVE_CURVE_OFFSET });
  });
});

describe("staggeredSupportEnd", () => {
  test("staggers along the aux-to-target line without a move control point", () => {
    expect(
      staggeredSupportEnd({ x: 0, y: 0 }, { x: 10, y: 0 }, 0)
    ).toEqual({ x: 5.625, y: 0 });
  });

  test("staggers along the move's arrival tangent when given a control point", () => {
    expect(
      staggeredSupportEnd({ x: 0, y: 0 }, { x: 10, y: 0 }, 0, { x: 10, y: 10 })
    ).toEqual({ x: 10, y: 4.375 });
  });
});

describe("buildConvoyRoute", () => {
  test("threads waypoints through ordered fleets with attachment points", () => {
    const route = buildConvoyRoute(
      { x: 0, y: 0 },
      { x: 30, y: 0 },
      [
        { id: "f2", point: { x: 20, y: 0 } },
        { id: "f1", point: { x: 10, y: 0 } },
      ]
    );
    expect(route.waypoints).toEqual([
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 20, y: 0 },
      { x: 30, y: 0 },
    ]);
    expect([...route.attachments.keys()]).toEqual(["f1", "f2"]);
  });

  test("falls back to a direct route when there are no fleets", () => {
    const route = buildConvoyRoute({ x: 0, y: 0 }, { x: 30, y: 0 }, []);
    expect(route.waypoints).toEqual([
      { x: 0, y: 0 },
      { x: 30, y: 0 },
    ]);
    expect(route.attachments.size).toBe(0);
  });
});
