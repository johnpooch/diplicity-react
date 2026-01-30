import paper from "paper";
import type { Position } from "@/types/variant";

paper.setup(new paper.Size(1, 1));

export function calculateCentroid(pathD: string): Position {
  const path = new paper.Path(pathD);
  const center = path.bounds.center;
  return { x: center.x, y: center.y };
}

export function calculatePositions(centroid: Position): {
  unitPosition: Position;
  dislodgedUnitPosition: Position;
  supplyCenterPosition: Position;
} {
  return {
    unitPosition: { x: centroid.x, y: centroid.y },
    dislodgedUnitPosition: { x: centroid.x + 15, y: centroid.y + 15 },
    supplyCenterPosition: { x: centroid.x - 12, y: centroid.y - 12 },
  };
}

export function detectPathIntersections(pathA: string, pathB: string): boolean {
  const paperPathA = new paper.Path(pathA);
  const paperPathB = new paper.Path(pathB);
  const intersections = paperPathA.getIntersections(paperPathB);
  return intersections.length >= 2;
}
