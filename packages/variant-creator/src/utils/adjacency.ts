import type { Province } from "@/types/variant";
import { detectPathIntersections } from "./geometry";

export interface AdjacencyMap {
  [provinceId: string]: string[];
}

export function detectAllAdjacencies(provinces: Province[]): AdjacencyMap {
  const adjacencyMap: AdjacencyMap = {};

  provinces.forEach((p) => {
    adjacencyMap[p.id] = [];
  });

  for (let i = 0; i < provinces.length; i++) {
    for (let j = i + 1; j < provinces.length; j++) {
      const provinceA = provinces[i];
      const provinceB = provinces[j];

      if (detectPathIntersections(provinceA.path, provinceB.path)) {
        adjacencyMap[provinceA.id].push(provinceB.id);
        adjacencyMap[provinceB.id].push(provinceA.id);
      }
    }
  }

  return adjacencyMap;
}

export function syncAdjacenciesToProvinces(
  provinces: Province[],
  adjacencyMap: AdjacencyMap
): Province[] {
  return provinces.map((province) => ({
    ...province,
    adjacencies: adjacencyMap[province.id] ?? [],
  }));
}

export function buildAdjacencyMapFromProvinces(
  provinces: Province[]
): AdjacencyMap {
  const adjacencyMap: AdjacencyMap = {};
  provinces.forEach((p) => {
    adjacencyMap[p.id] = [...p.adjacencies];
  });
  return adjacencyMap;
}

export function toggleAdjacency(
  adjacencyMap: AdjacencyMap,
  provinceIdA: string,
  provinceIdB: string
): AdjacencyMap {
  const newMap: AdjacencyMap = {};
  Object.keys(adjacencyMap).forEach((key) => {
    newMap[key] = [...adjacencyMap[key]];
  });

  if (!newMap[provinceIdA]) newMap[provinceIdA] = [];
  if (!newMap[provinceIdB]) newMap[provinceIdB] = [];

  const indexInA = newMap[provinceIdA].indexOf(provinceIdB);

  if (indexInA >= 0) {
    newMap[provinceIdA] = newMap[provinceIdA].filter((id) => id !== provinceIdB);
    newMap[provinceIdB] = newMap[provinceIdB].filter((id) => id !== provinceIdA);
  } else {
    newMap[provinceIdA] = [...newMap[provinceIdA], provinceIdB];
    newMap[provinceIdB] = [...newMap[provinceIdB], provinceIdA];
  }

  return newMap;
}

export function getIsolatedProvinces(
  provinces: Province[],
  adjacencyMap: AdjacencyMap
): Province[] {
  return provinces.filter(
    (p) => !adjacencyMap[p.id] || adjacencyMap[p.id].length === 0
  );
}
