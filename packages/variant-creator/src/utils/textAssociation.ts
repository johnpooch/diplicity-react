import type { TextElement, Province, Label } from "@/types/variant";
import { calculateCentroid } from "./geometry";

const ASSOCIATION_THRESHOLD = 100;

export function autoAssociateText(
  textElements: TextElement[],
  provinces: Province[]
): Map<number, string | null> {
  const associations = new Map<number, string | null>();

  const provinceCentroids = provinces.map((province) => ({
    id: province.id,
    centroid: calculateCentroid(province.path),
  }));

  textElements.forEach((text, index) => {
    let closestProvinceId: string | null = null;
    let closestDistance = Infinity;

    provinceCentroids.forEach(({ id, centroid }) => {
      const distance = Math.hypot(text.x - centroid.x, text.y - centroid.y);

      if (distance < closestDistance && distance < ASSOCIATION_THRESHOLD) {
        closestDistance = distance;
        closestProvinceId = id;
      }
    });

    associations.set(index, closestProvinceId);
  });

  return associations;
}

export function textElementToLabel(text: TextElement): Label {
  return {
    text: text.content,
    position: { x: text.x, y: text.y },
    rotation: text.rotation,
    source: "svg",
    styles: text.styles,
  };
}

export function syncAssociationsToProvinces(
  textElements: TextElement[],
  provinces: Province[],
  associations: Map<number, string | null>
): Province[] {
  const provinceLabelsMap = new Map<string, Label[]>();

  provinces.forEach((province) => {
    const existingNonSvgLabels = province.labels.filter(
      (label) => label.source !== "svg"
    );
    provinceLabelsMap.set(province.id, existingNonSvgLabels);
  });

  associations.forEach((provinceId, textIndex) => {
    if (provinceId !== null) {
      const text = textElements[textIndex];
      const label = textElementToLabel(text);
      const existingLabels = provinceLabelsMap.get(provinceId) ?? [];
      provinceLabelsMap.set(provinceId, [...existingLabels, label]);
    }
  });

  return provinces.map((province) => ({
    ...province,
    labels: provinceLabelsMap.get(province.id) ?? province.labels,
  }));
}

export function buildAssociationsFromProvinces(
  textElements: TextElement[],
  provinces: Province[]
): Map<number, string | null> {
  const associations = new Map<number, string | null>();

  textElements.forEach((_, index) => {
    associations.set(index, null);
  });

  provinces.forEach((province) => {
    province.labels
      .filter((label) => label.source === "svg")
      .forEach((label) => {
        const textIndex = textElements.findIndex(
          (text) =>
            text.content === label.text &&
            text.x === label.position.x &&
            text.y === label.position.y
        );
        if (textIndex !== -1) {
          associations.set(textIndex, province.id);
        }
      });
  });

  return associations;
}
