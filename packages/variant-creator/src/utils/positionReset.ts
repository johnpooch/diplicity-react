import type { Province, Position } from "@/types/variant";
import { calculateCentroid, calculatePositions } from "./geometry";

export function resetToAutoPosition(province: Province): {
  unitPosition: Position;
  dislodgedUnitPosition: Position;
  supplyCenterPosition: Position;
} {
  const centroid = calculateCentroid(province.path);
  return calculatePositions(centroid);
}

export function resetLabelToAutoPosition(province: Province): Position {
  return calculateCentroid(province.path);
}
