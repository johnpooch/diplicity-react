import { flattenPath } from "./pathFlatten";

export type Rect = { minX: number; minY: number; maxX: number; maxY: number };

// Padded bounding rectangle (in viewBox space) of the given provinces' path
// geometry, or null if none of the ids have a known path. The rasterised base
// has no per-province elements to measure, so the box is derived from the same
// path strings that drive the hit-test rings. padding scales the box about its
// centre (1 = tight, 1.4 = 40% margin).
export const focusBounds = (
  paths: Map<string, string>,
  ids: string[],
  padding = 1.4
): Rect | null => {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const id of ids) {
    const d = paths.get(id);
    if (!d) continue;
    for (const ring of flattenPath(d)) {
      for (const point of ring) {
        minX = Math.min(minX, point.x);
        minY = Math.min(minY, point.y);
        maxX = Math.max(maxX, point.x);
        maxY = Math.max(maxY, point.y);
      }
    }
  }
  if (!isFinite(minX)) return null;
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const halfWidth = ((maxX - minX) / 2) * padding;
  const halfHeight = ((maxY - minY) / 2) * padding;
  return {
    minX: centerX - halfWidth,
    minY: centerY - halfHeight,
    maxX: centerX + halfWidth,
    maxY: centerY + halfHeight,
  };
};
