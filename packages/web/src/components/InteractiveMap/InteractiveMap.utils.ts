// Helper function to compute the projection of point (x1, y1) onto the line (x2, y2) -> (x3, y3)
const getClosestPointOnLine = (
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  x3: number,
  y3: number
) => {
  // Line vector (x2, y2) -> (x3, y3)
  const lineVecX = x3 - x2;
  const lineVecY = y3 - y2;

  // Point vector (x2, y2) -> (x1, y1)
  const pointVecX = x1 - x2;
  const pointVecY = y1 - y2;

  // Project point onto the line
  const lineLengthSquared = lineVecX * lineVecX + lineVecY * lineVecY;
  const projection =
    (pointVecX * lineVecX + pointVecY * lineVecY) / lineLengthSquared;

  // Closest point on the line
  const closestX = x2 + projection * lineVecX;
  const closestY = y2 + projection * lineVecY;

  return { x: closestX, y: closestY };
};

export { getClosestPointOnLine };
