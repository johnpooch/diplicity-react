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

  // Project point onto the line segment, clamped to [0, 1]
  const lineLengthSquared = lineVecX * lineVecX + lineVecY * lineVecY;
  const t = Math.max(
    0.1,
    Math.min(
      0.9,
      (pointVecX * lineVecX + pointVecY * lineVecY) / lineLengthSquared
    )
  );

  // Closest point on the segment
  const closestX = x2 + t * lineVecX;
  const closestY = y2 + t * lineVecY;

  return { x: closestX, y: closestY };
};

export { getClosestPointOnLine };
