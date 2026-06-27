import { describe, it, expect } from "vitest";
import { buildProvinceRings } from "./provincePolygons";

describe("buildProvinceRings", () => {
  it("produces one decimated ring per province path", () => {
    const paths = new Map([["par", "M 0 0 L 10 0 L 10 10 L 0 10 Z"]]);
    const rings = buildProvinceRings(paths, 1);
    expect(rings).toHaveLength(1);
    expect(rings[0].id).toBe("par");
    expect(rings[0].points.length).toBeGreaterThanOrEqual(3);
  });

  it("emits a separate ring for each subpath, sharing the province id", () => {
    const paths = new Map([
      ["isl", "M 0 0 L 4 0 L 4 4 Z M 20 20 L 24 20 L 24 24 Z"],
    ]);
    const rings = buildProvinceRings(paths, 1);
    expect(rings).toHaveLength(2);
    expect(rings.every((ring) => ring.id === "isl")).toBe(true);
  });

  it("drops rings that collapse below a triangle after decimation", () => {
    const paths = new Map([["tiny", "M 0 0 L 1 1 Z"]]);
    const rings = buildProvinceRings(paths, 5);
    expect(rings).toHaveLength(0);
  });

  it("decimates a dense near-straight edge", () => {
    const dense = ["M 0 0"];
    for (let x = 1; x <= 40; x++) {
      dense.push(`L ${x} ${x % 2 === 0 ? 0.1 : -0.1}`);
    }
    dense.push("L 40 40 L 0 40 Z");
    const rings = buildProvinceRings(new Map([["p", dense.join(" ")]]), 1);
    expect(rings[0].points.length).toBeLessThan(40);
  });
});
