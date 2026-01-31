import type { Dimensions } from "@/types/variant";

const MIN_MAX_HEIGHT_VH = 40;
const MAX_MAX_HEIGHT_VH = 70;
const SQUARE_MAX_HEIGHT_VH = 50;

export function calculateMapMaxHeight(dimensions: Dimensions): string {
  const aspectRatio = dimensions.width / dimensions.height;

  let maxHeightVh: number;

  if (aspectRatio >= 1) {
    // Landscape: 50vh (square) → 40vh (wide)
    const t = Math.min((aspectRatio - 1) / 0.5, 1);
    maxHeightVh = SQUARE_MAX_HEIGHT_VH - t * (SQUARE_MAX_HEIGHT_VH - MIN_MAX_HEIGHT_VH);
  } else {
    // Portrait: 50vh (square) → 70vh (tall)
    const t = Math.min((1 - aspectRatio) / 0.5, 1);
    maxHeightVh = SQUARE_MAX_HEIGHT_VH + t * (MAX_MAX_HEIGHT_VH - SQUARE_MAX_HEIGHT_VH);
  }

  return `${Math.round(maxHeightVh)}vh`;
}
