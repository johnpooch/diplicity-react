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
  controlPoint?: { x: number; y: number };
  onRenderCenter?: (x: number, y: number, angle: number) => React.ReactElement;
};

const Arrow = (props: ArrowProps) => {
  if (props.controlPoint) {
    const { x: cx, y: cy } = props.controlPoint;

    // Initial tangent: from (x1,y1) toward control point
    const startDx = cx - props.x1;
    const startDy = cy - props.y1;
    const startLen = Math.sqrt(startDx * startDx + startDy * startDy);
    const startX = props.x1 + (startDx / startLen) * props.offset;
    const startY = props.y1 + (startDy / startLen) * props.offset;

    // End tangent: from control point toward (x2,y2)
    const endDx = props.x2 - cx;
    const endDy = props.y2 - cy;
    const endLen = Math.sqrt(endDx * endDx + endDy * endDy);
    const etx = endDx / endLen;
    const ety = endDy / endLen;
    const endAngle = Math.atan2(ety, etx);

    // Arrowhead tip: offset back from end along end tangent
    const tipX = props.x2 - etx * props.offset;
    const tipY = props.y2 - ety * props.offset;

    // Line end (base of arrowhead)
    const endX = tipX - etx * props.arrowLength;
    const endY = tipY - ety * props.arrowLength;

    const perpAngle = endAngle + Math.PI / 2;
    const arrowStart = {
      x: endX - (props.lineWidth / 2) * Math.cos(perpAngle),
      y: endY - (props.lineWidth / 2) * Math.sin(perpAngle),
    };
    const arrowEnd = {
      x: endX + (props.lineWidth / 2) * Math.cos(perpAngle),
      y: endY + (props.lineWidth / 2) * Math.sin(perpAngle),
    };
    const arrowBottomLeft = {
      x: endX - props.arrowWidth * Math.cos(perpAngle),
      y: endY - props.arrowWidth * Math.sin(perpAngle),
    };
    const arrowBottomRight = {
      x: endX + props.arrowWidth * Math.cos(perpAngle),
      y: endY + props.arrowWidth * Math.sin(perpAngle),
    };

    // Center at t=0.5 of the quadratic Bezier: 0.25*P0 + 0.5*P1 + 0.25*P2
    const centerX = 0.25 * props.x1 + 0.5 * cx + 0.25 * props.x2;
    const centerY = 0.25 * props.y1 + 0.5 * cy + 0.25 * props.y2;
    // Tangent at t=0.5 of quadratic Bezier = P2-P0 direction
    const centerAngle = Math.atan2(props.y2 - props.y1, props.x2 - props.x1);

    const dashArray = props.dash
      ? `${props.dash.length} ${props.dash.spacing}`
      : "none";

    return (
      <g>
        <path
          d={`M ${startX} ${startY} Q ${cx} ${cy} ${endX} ${endY}`}
          stroke={props.stroke}
          strokeWidth={props.lineWidth + props.strokeWidth * 2}
          fill="none"
          strokeDasharray={dashArray}
        />
        <path
          d={`M ${startX} ${startY} Q ${cx} ${cy} ${endX} ${endY}`}
          stroke={props.fill}
          strokeWidth={props.lineWidth}
          fill="none"
          strokeDasharray={dashArray}
        />
        <path
          d={`M ${arrowStart.x} ${arrowStart.y} L ${arrowBottomLeft.x} ${arrowBottomLeft.y} L ${tipX} ${tipY} L ${arrowBottomRight.x} ${arrowBottomRight.y} L ${arrowEnd.x} ${arrowEnd.y}`}
          stroke={props.stroke}
          strokeWidth={props.strokeWidth}
          fill={props.fill}
        />
        {props.onRenderCenter &&
          props.onRenderCenter(centerX, centerY, centerAngle)}
      </g>
    );
  }

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

  const centerX = (startX + endX) / 2;
  const centerY = (startY + endY) / 2;

  const arrowStart = {
    x: endX - (props.lineWidth / 2) * Math.cos(angle + Math.PI / 2),
    y: endY - (props.lineWidth / 2) * Math.sin(angle + Math.PI / 2),
  };

  const arrowEnd = {
    x: endX + (props.lineWidth / 2) * Math.cos(angle + Math.PI / 2),
    y: endY + (props.lineWidth / 2) * Math.sin(angle + Math.PI / 2),
  };

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
      {props.onRenderCenter && props.onRenderCenter(centerX, centerY, angle)}
    </g>
  );
};

export { Arrow };
