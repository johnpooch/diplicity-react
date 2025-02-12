import React from "react";

type CrossProps = {
  x: number;
  y: number;
  width: number;
  length: number;
  angle: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
};

const Cross = ({
  x,
  y,
  width,
  length,
  angle,
  fill,
  stroke,
  strokeWidth,
}: CrossProps) => {
  // Convert angle from degrees to radians
  const angleRad = (angle * Math.PI) / 180;

  // Define the points for the cross shape (moving clockwise from top)
  const points = [
    // Top vertical arm
    [-width / 2, -length], // Top left
    [width / 2, -length], // Top right
    [width / 2, -width / 2], // Inner top right
    [length, -width / 2], // Right arm outer top
    [length, width / 2], // Right arm outer bottom
    [width / 2, width / 2], // Inner right bottom
    [width / 2, length], // Bottom right
    [-width / 2, length], // Bottom left
    [-width / 2, width / 2], // Inner bottom left
    [-length, width / 2], // Left arm outer bottom
    [-length, -width / 2], // Left arm outer top
    [-width / 2, -width / 2], // Inner top left
  ];

  // Function to rotate a point around origin and translate to final position
  const transformPoint = (point: number[]): string => {
    const [px, py] = point;
    const rotatedX = px * Math.cos(angleRad) - py * Math.sin(angleRad) + x;
    const rotatedY = px * Math.sin(angleRad) + py * Math.cos(angleRad) + y;
    return `${rotatedX} ${rotatedY}`;
  };

  // Create path data by rotating and translating all points
  const pathData = `
    M ${transformPoint(points[0])}
    ${points
      .slice(1)
      .map((point) => `L ${transformPoint(point)}`)
      .join(" ")}
    Z
  `;

  return (
    <g>
      <path
        d={pathData}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
      />
    </g>
  );
};

export { Cross };
