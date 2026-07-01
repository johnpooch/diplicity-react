import type { Point } from "../InteractiveMap/dsvgParser";
import { flattenPath } from "./pathFlatten";
import { decimate } from "./decimate";

export const HIT_TEST_TOLERANCE = 5;

export type ProvinceRing = {
  id: string;
  points: Point[];
};

// Turns the dSVG province / named-coast path strings into decimated polygon
// rings keyed by province id. Each subpath becomes its own ring so that islands
// and multi-part provinces hit-test correctly. Rings that collapse below a
// triangle after decimation are dropped.
export const buildProvinceRings = (
  paths: Map<string, string>,
  tolerance: number = HIT_TEST_TOLERANCE
): ProvinceRing[] => {
  const rings: ProvinceRing[] = [];
  for (const [id, d] of paths) {
    for (const ring of flattenPath(d)) {
      const simplified = decimate(ring, tolerance);
      if (simplified.length >= 3) {
        rings.push({ id, points: simplified });
      }
    }
  }
  return rings;
};
