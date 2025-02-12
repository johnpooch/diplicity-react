import { Cross } from "./cross";

// Ensures that arrow starts and ends at the edge of the source and target unit
const UNIT_RADIUS_OFFSET = 10;

const CROSS_SIZE = 10;

type MoveArrowProps = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  failed?: boolean;
};

type SupportArrowProps = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  x3: number;
  y3: number;
  failed?: boolean;
};

const MoveArrow = (props: MoveArrowProps) => {
  const dx = props.x2 - props.x1;
  const dy = props.y2 - props.y1;

  const length = Math.sqrt(dx * dx + dy * dy);

  const offsetX = (dx / length) * UNIT_RADIUS_OFFSET;
  const offsetY = (dy / length) * UNIT_RADIUS_OFFSET;

  const startX = props.x1 + offsetX;
  const startY = props.y1 + offsetY;

  const endX = props.x2 - offsetX;
  const endY = props.y2 - offsetY;

  const midX = (startX + endX) / 2;
  const midY = (startY + endY) / 2;

  const crossAngle = Math.atan2(dy, dx) * (180 / Math.PI);

  const path = `M ${startX} ${startY} L ${endX} ${endY}`;

  return (
    <g>
      <path
        d={path}
        fill="none"
        stroke="black"
        strokeWidth={3}
        markerEnd="url(#arrowhead)"
      />
      <Cross
        x={midX}
        y={midY}
        width={CROSS_SIZE}
        length={CROSS_SIZE}
        angle={crossAngle}
        stroke="black"
        strokeWidth={3}
        fill="red"
      />
    </g>
  );
};

const SupportArrow = (props: SupportArrowProps) => {
  const dx = props.x2 - props.x1;
  const dy = props.y2 - props.y1;

  const length = Math.sqrt(dx * dx + dy * dy);

  const offsetX = (dx / length) * UNIT_RADIUS_OFFSET;
  const offsetY = (dy / length) * UNIT_RADIUS_OFFSET;

  const startX = props.x1 + offsetX;
  const startY = props.y1 + offsetY;

  const endX = props.x2 - offsetX;
  const endY = props.y2 - offsetY;

  // Calculate control point for the quadratic Bezier curve
  const controlX = props.x3;
  const controlY = props.y3;

  // Define the path using a quadratic Bezier curve
  const path = `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;

  // Calculate the midpoint of the quadratic Bezier curve
  const t = 0.5;
  const midX =
    (1 - t) * (1 - t) * startX + 2 * (1 - t) * t * controlX + t * t * endX;
  const midY =
    (1 - t) * (1 - t) * startY + 2 * (1 - t) * t * controlY + t * t * endY;

  // Rotate the cross to be perpendicular to the line
  const crossAngle = Math.atan2(dy, dx) * (180 / Math.PI);

  return (
    <g>
      <path
        d={path}
        fill="none"
        stroke="black"
        strokeWidth={3}
        strokeDasharray="5,5"
        markerEnd="url(#arrowhead)"
      />
      {/* <Cross
        x={midX}
        y={midY}
        width={CROSS_SIZE}
        length={CROSS_SIZE}
        angle={crossAngle}
        stroke="black"
        strokeWidth={3}
        fill="red"
      /> */}
    </g>
  );
};

export { MoveArrow, SupportArrow };
