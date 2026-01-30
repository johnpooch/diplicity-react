import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../geometry", () => ({
  detectPathIntersections: vi.fn((pathA: string, pathB: string) => {
    if (pathA.includes("adjacent-to-b") && pathB.includes("province-b")) {
      return true;
    }
    if (pathA.includes("province-b") && pathB.includes("adjacent-to-b")) {
      return true;
    }
    if (pathA.includes("adjacent-to-c") && pathB.includes("province-c")) {
      return true;
    }
    if (pathA.includes("province-c") && pathB.includes("adjacent-to-c")) {
      return true;
    }
    return false;
  }),
}));

import {
  detectAllAdjacencies,
  syncAdjacenciesToProvinces,
  buildAdjacencyMapFromProvinces,
  toggleAdjacency,
  getIsolatedProvinces,
} from "../adjacency";
import type { Province } from "@/types/variant";

const createMockProvince = (
  id: string,
  path: string,
  adjacencies: string[] = []
): Province => ({
  id,
  elementId: `element-${id}`,
  name: id.toUpperCase(),
  type: "land",
  path,
  homeNation: null,
  supplyCenter: false,
  startingUnit: null,
  adjacencies,
  labels: [],
  unitPosition: { x: 0, y: 0 },
  dislodgedUnitPosition: { x: 0, y: 0 },
});

describe("detectAllAdjacencies", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("detects adjacencies between provinces", () => {
    const provinces: Province[] = [
      createMockProvince("a", "M0,0 adjacent-to-b L10,0 Z"),
      createMockProvince("b", "M10,0 province-b adjacent-to-c L20,0 Z"),
      createMockProvince("c", "M20,0 province-c L30,0 Z"),
    ];

    const result = detectAllAdjacencies(provinces);

    expect(result.a).toContain("b");
    expect(result.b).toContain("a");
    expect(result.b).toContain("c");
    expect(result.c).toContain("b");
    expect(result.a).not.toContain("c");
    expect(result.c).not.toContain("a");
  });

  it("returns empty arrays for non-adjacent provinces", () => {
    const provinces: Province[] = [
      createMockProvince("isolated1", "M0,0 L10,0 Z"),
      createMockProvince("isolated2", "M100,0 L110,0 Z"),
    ];

    const result = detectAllAdjacencies(provinces);

    expect(result.isolated1).toEqual([]);
    expect(result.isolated2).toEqual([]);
  });

  it("handles empty province array", () => {
    const result = detectAllAdjacencies([]);
    expect(result).toEqual({});
  });
});

describe("syncAdjacenciesToProvinces", () => {
  it("applies adjacency map to provinces", () => {
    const provinces: Province[] = [
      createMockProvince("a", "path-a"),
      createMockProvince("b", "path-b"),
    ];

    const adjacencyMap = {
      a: ["b"],
      b: ["a"],
    };

    const result = syncAdjacenciesToProvinces(provinces, adjacencyMap);

    expect(result[0].adjacencies).toEqual(["b"]);
    expect(result[1].adjacencies).toEqual(["a"]);
  });

  it("handles missing entries in adjacency map", () => {
    const provinces: Province[] = [
      createMockProvince("a", "path-a"),
      createMockProvince("b", "path-b"),
    ];

    const adjacencyMap = {
      a: ["b"],
    };

    const result = syncAdjacenciesToProvinces(provinces, adjacencyMap);

    expect(result[0].adjacencies).toEqual(["b"]);
    expect(result[1].adjacencies).toEqual([]);
  });
});

describe("buildAdjacencyMapFromProvinces", () => {
  it("builds map from existing province adjacencies", () => {
    const provinces: Province[] = [
      createMockProvince("a", "path-a", ["b", "c"]),
      createMockProvince("b", "path-b", ["a"]),
      createMockProvince("c", "path-c", ["a"]),
    ];

    const result = buildAdjacencyMapFromProvinces(provinces);

    expect(result.a).toEqual(["b", "c"]);
    expect(result.b).toEqual(["a"]);
    expect(result.c).toEqual(["a"]);
  });

  it("creates independent copy of adjacencies array", () => {
    const provinces: Province[] = [createMockProvince("a", "path-a", ["b"])];

    const result = buildAdjacencyMapFromProvinces(provinces);
    result.a.push("c");

    expect(provinces[0].adjacencies).toEqual(["b"]);
  });
});

describe("toggleAdjacency", () => {
  it("adds adjacency bidirectionally when not present", () => {
    const adjacencyMap = {
      a: [],
      b: [],
    };

    const result = toggleAdjacency(adjacencyMap, "a", "b");

    expect(result.a).toContain("b");
    expect(result.b).toContain("a");
  });

  it("removes adjacency bidirectionally when present", () => {
    const adjacencyMap = {
      a: ["b"],
      b: ["a"],
    };

    const result = toggleAdjacency(adjacencyMap, "a", "b");

    expect(result.a).not.toContain("b");
    expect(result.b).not.toContain("a");
  });

  it("creates arrays for provinces not in map", () => {
    const adjacencyMap = {};

    const result = toggleAdjacency(adjacencyMap, "x", "y");

    expect(result.x).toContain("y");
    expect(result.y).toContain("x");
  });

  it("does not mutate original map", () => {
    const adjacencyMap = {
      a: ["c"],
      b: [],
    };

    const result = toggleAdjacency(adjacencyMap, "a", "b");

    expect(adjacencyMap.a).toEqual(["c"]);
    expect(adjacencyMap.b).toEqual([]);
    expect(result.a).toContain("b");
    expect(result.a).toContain("c");
  });
});

describe("getIsolatedProvinces", () => {
  it("returns provinces with no adjacencies", () => {
    const provinces: Province[] = [
      createMockProvince("connected", "path-a"),
      createMockProvince("isolated", "path-b"),
    ];

    const adjacencyMap = {
      connected: ["other"],
      isolated: [],
    };

    const result = getIsolatedProvinces(provinces, adjacencyMap);

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("isolated");
  });

  it("handles provinces missing from adjacency map", () => {
    const provinces: Province[] = [
      createMockProvince("a", "path-a"),
      createMockProvince("missing", "path-b"),
    ];

    const adjacencyMap = {
      a: ["b"],
    };

    const result = getIsolatedProvinces(provinces, adjacencyMap);

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("missing");
  });

  it("returns empty array when all provinces have adjacencies", () => {
    const provinces: Province[] = [
      createMockProvince("a", "path-a"),
      createMockProvince("b", "path-b"),
    ];

    const adjacencyMap = {
      a: ["b"],
      b: ["a"],
    };

    const result = getIsolatedProvinces(provinces, adjacencyMap);

    expect(result).toHaveLength(0);
  });
});
