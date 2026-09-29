import { describe, test, expect } from "vitest";
import {
  euclidean,
  wrappedEuclidean,
  closestPointOnLine,
  bSplineAttachmentPoint,
  shortestWaypointOrder,
  headToHeadControlPoint,
  staggeredSupportEnd,
  buildConvoyRoute,
  EXACT_WAYPOINT_LIMIT,
  MOVE_CURVE_OFFSET,
} from "./orderGeometry";

describe("euclidean", () => {
  test("measures the distance between two points", () => {
    expect(euclidean({ x: 0, y: 0 }, { x: 3, y: 4 })).toBe(5);
  });
});

describe("wrappedEuclidean", () => {
  test("measures across the horizontal seam when it is shorter", () => {
    expect(
      wrappedEuclidean({ x: 950, y: 0 }, { x: 50, y: 0 }, 1000)
    ).toBe(100);
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

  test("finds the exact shortest route without enumerating every permutation", () => {
    const items = [
      { id: "c", point: { x: 30, y: 0 } },
      { id: "a", point: { x: 10, y: 0 } },
      { id: "d", point: { x: 40, y: 0 } },
      { id: "b", point: { x: 20, y: 0 } },
    ];
    const ordered = shortestWaypointOrder(
      items,
      (item) => item.point,
      { x: 0, y: 0 },
      { x: 50, y: 0 }
    );
    expect(ordered.map((item) => item.id)).toEqual(["a", "b", "c", "d"]);
  });

  test("keeps exceptionally large custom convoys bounded and deterministic", () => {
    const items = Array.from(
      { length: EXACT_WAYPOINT_LIMIT + 1 },
      (_, index) => ({
        id: String(index),
        point: { x: (index + 1) * 10, y: 0 },
      })
    ).reverse();
    const ordered = shortestWaypointOrder(
      items,
      (item) => item.point,
      { x: 0, y: 0 },
      { x: 150, y: 0 }
    );
    expect(ordered.map((item) => item.id)).toEqual(
      Array.from({ length: EXACT_WAYPOINT_LIMIT + 1 }, (_, index) =>
        String(index)
      )
    );
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

  test("unwraps a convoy route continuously across the horizontal seam", () => {
    const route = buildConvoyRoute(
      { x: 900, y: 0 },
      { x: 100, y: 0 },
      [{ id: "fleet", point: { x: 980, y: 0 } }],
      1000
    );
    expect(route.waypoints).toEqual([
      { x: 900, y: 0 },
      { x: 980, y: 0 },
      { x: 1100, y: 0 },
    ]);
  });

  test("follows the Continental Drift convoy chain around the left seam", () => {
    const route = buildConvoyRoute(
      { x: 834.5, y: 722.6 },
      { x: 2140.9, y: 775.3 },
      [
        { id: "mao", point: { x: 1105.9, y: 733.4 } },
        { id: "sao", point: { x: 1171.4, y: 1079.9 } },
        { id: "sco", point: { x: 758.6, y: 1295.6 } },
        { id: "epo", point: { x: 616.6, y: 827.1 } },
        { id: "mpo", point: { x: 2602.5, y: 755.2 } },
        { id: "scs", point: { x: 2183.2, y: 669.7 } },
      ],
      2625.5
    );

    expect([...route.attachments.keys()]).toEqual([
      "mao",
      "sao",
      "sco",
      "epo",
      "mpo",
      "scs",
    ]);
    expect(route.waypoints.at(-1)?.x).toBeCloseTo(-484.6);
  });
});
