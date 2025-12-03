import { Octagon } from "../shapes/octagon";

type SupportHoldArrowProps = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  lineWidth: number;
  arrowWidth: number;
  arrowLength: number;
  offset: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  dash?: { length: number; spacing: number };
  onRenderCenter?: (x: number, y: number, angle: number) => React.ReactElement;
};

const SupportHoldArrow = (props: SupportHoldArrowProps) => {
  // Calculate the angle of the line
  const angle = Math.atan2(props.y2 - props.y1, props.x2 - props.x1);
  // Calculate the offset points
  const offsetX = props.offset * Math.cos(angle);
  const offsetY = props.offset * Math.sin(angle);
  // Adjust start and end points by offset
  const startX = props.x1 + offsetX;
  const startY = props.y1 + offsetY;
  const endX = props.x2 - offsetX - Math.cos(angle);
  const endY = props.y2 - offsetY - Math.sin(angle);
  const centerX = (startX + endX) / 2;
  const centerY = (startY + endY) / 2;
  return (
    <g>
      <path
        d={`M ${startX} ${startY} L ${endX} ${endY}`}
        stroke={props.stroke}
        strokeWidth={props.lineWidth + props.strokeWidth * 2}
        strokeDasharray={
          props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
        }
      />
      <path
        d={`M ${startX} ${startY} L ${endX} ${endY}`}
        stroke={props.fill}
        strokeWidth={props.lineWidth}
        strokeDasharray={
          props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
        }
      />
      {props.onRenderCenter && props.onRenderCenter(centerX, centerY, angle)}
      <Octagon
        x={endX}
        y={endY}
        size={8}
        stroke={props.stroke}
        fill={props.fill}
        strokeWidth={3}
      />
    </g>
  );
};

export { SupportHoldArrow };
