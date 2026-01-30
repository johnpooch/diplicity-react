import type { ParsedSvg, VariantDefinition, Province } from "@/types/variant";
import { calculateCentroid, calculatePositions } from "./geometry";

export function createInitialVariant(parsedSvg: ParsedSvg): VariantDefinition {
  const provinces: Province[] = parsedSvg.provincePaths.map((path, index) => {
    const elementId = path.elementId ?? `province_${index}`;
    const centroid = calculateCentroid(path.d);
    const positions = calculatePositions(centroid);

    return {
      id: elementId,
      elementId,
      name: "",
      type: "land",
      path: path.d,
      homeNation: null,
      supplyCenter: false,
      startingUnit: null,
      adjacencies: [],
      labels: [],
      unitPosition: positions.unitPosition,
      dislodgedUnitPosition: positions.dislodgedUnitPosition,
      supplyCenterPosition: positions.supplyCenterPosition,
    };
  });

  return {
    name: "",
    description: "",
    author: "",
    version: "1.0.0",
    soloVictorySCCount: 0,
    nations: [],
    provinces,
    namedCoasts: [],
    decorativeElements: parsedSvg.decorativeElements,
    dimensions: parsedSvg.dimensions,
    textElements: parsedSvg.textElements,
  };
}
