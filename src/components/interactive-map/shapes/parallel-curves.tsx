import React from "react";

interface ParallelCurvesProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  x3: number;
  y3: number;
  lineWidth: number;
  offset: number;
}

const ParallelCurves: React.FC<ParallelCurvesProps> = ({
  x1,
  y1,
  x2,
  y2,
  x3,
  y3,
  lineWidth,
  offset,
}) => {
  // Function to compute perpendicular offset
  const getOffsetPoint = (
    x: number,
    y: number,
    angle: number,
    distance: number
  ) => ({
    x: x + Math.cos(angle) * distance,
    y: y + Math.sin(angle) * distance,
  });

  // Compute angles for the curve directions
  const angle1 = Math.atan2(y2 - y1, x2 - x1);
  const angle2 = Math.atan2(y3 - y2, x3 - x2);

  // Offset start and end points
  const start1 = getOffsetPoint(x1, y1, angle1, offset);
  const end1 = getOffsetPoint(x3, y3, angle2, -offset);

  // Compute perpendicular vector for parallel lines
  const perpAngle = angle1 + Math.PI / 2; // Perpendicular direction
  const start2 = getOffsetPoint(start1.x, start1.y, perpAngle, lineWidth);
  const end2 = getOffsetPoint(end1.x, end1.y, perpAngle, lineWidth);

  return (
    <g>
      {/* First curved line */}
      <path
        d={`M${start1.x},${start1.y} Q${x2},${y2} ${end1.x},${end1.y}`}
        stroke="blue"
        strokeWidth="2"
        fill="none"
      />
      {/* Parallel curved line */}
      <path
        d={`M${start2.x},${start2.y} Q${x2 + Math.cos(perpAngle) * lineWidth},${
          y2 + Math.sin(perpAngle) * lineWidth
        } ${end2.x},${end2.y}`}
        stroke="blue"
        strokeWidth="2"
        fill="none"
      />
    </g>
  );
};

export { ParallelCurves };
