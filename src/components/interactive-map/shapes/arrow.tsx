type ArrowProps = {
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

const Arrow = (props: ArrowProps) => {
  // Calculate the angle of the line
  const angle = Math.atan2(props.y2 - props.y1, props.x2 - props.x1);

  // Calculate the offset points
  const offsetX = props.offset * Math.cos(angle);
  const offsetY = props.offset * Math.sin(angle);

  // Adjust start and end points by offset
  const startX = props.x1 + offsetX;
  const startY = props.y1 + offsetY;

  const endX = props.x2 - offsetX - props.arrowLength * Math.cos(angle);
  const endY = props.y2 - offsetY - props.arrowLength * Math.sin(angle);

  const arrowStart = {
    x: endX - (props.lineWidth / 2) * Math.cos(angle + Math.PI / 2),
    y: endY - (props.lineWidth / 2) * Math.sin(angle + Math.PI / 2),
  };

  const arrowEnd = {
    x: endX + (props.lineWidth / 2) * Math.cos(angle + Math.PI / 2),
    y: endY + (props.lineWidth / 2) * Math.sin(angle + Math.PI / 2),
  };

  // Perpendicular to the line, 5 away from center base
  const arrowBottomLeft = {
    x: endX - props.arrowWidth * Math.cos(angle + Math.PI / 2),
    y: endY - props.arrowWidth * Math.sin(angle + Math.PI / 2),
  };

  const arrowBottomRight = {
    x: endX + props.arrowWidth * Math.cos(angle + Math.PI / 2),
    y: endY + props.arrowWidth * Math.sin(angle + Math.PI / 2),
  };

  const arrowTop = {
    x: endX + props.arrowLength * Math.cos(angle),
    y: endY + props.arrowLength * Math.sin(angle),
  };

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
      <path
        d={`M ${arrowStart.x} ${arrowStart.y} L ${arrowBottomLeft.x} ${arrowBottomLeft.y} L ${arrowTop.x} ${arrowTop.y} L ${arrowBottomRight.x} ${arrowBottomRight.y} L ${arrowEnd.x} ${arrowEnd.y} `}
        stroke={props.stroke}
        strokeWidth={props.strokeWidth}
        fill={props.fill}
      />
      {/* {props.onRenderCenter && props.onRenderCenter(centerX, centerY, angle)} */}
    </g>
  );
};

export { Arrow };
