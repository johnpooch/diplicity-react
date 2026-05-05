import React from "react";

type CurvedArrowProps = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  x3: number;
  y3: number;
  offset: number;
  fill: string;
  lineWidth: number;
  stroke: string;
  strokeWidth: number;
  arrowWidth: number;
  arrowLength: number;
  dash?: { length: number; spacing: number };
  // When the supported move curves (head-to-head), override the end direction so the
  // arrowhead aligns with the move arrow's arrival angle instead of the straight aux→target line.
  endControlPoint?: { x: number; y: number };
  onRenderCenter?: (x: number, y: number, angle: number) => React.ReactElement;
};

const getOffsetPoint = (
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  offset: number
) => {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  return {
    x: x1 + (dx / len) * offset,
    y: y1 + (dy / len) * offset,
  };
};

const getBezierPoint = (
  t: number,
  p0: { x: number; y: number },
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  p3: { x: number; y: number }
) => {
  const x =
    Math.pow(1 - t, 3) * p0.x +
    3 * Math.pow(1 - t, 2) * t * p1.x +
    3 * (1 - t) * Math.pow(t, 2) * p2.x +
    Math.pow(t, 3) * p3.x;
  const y =
    Math.pow(1 - t, 3) * p0.y +
    3 * Math.pow(1 - t, 2) * t * p1.y +
    3 * (1 - t) * Math.pow(t, 2) * p2.y +
    Math.pow(t, 3) * p3.y;
  return { x, y };
};

const CurvedArrow: React.FC<CurvedArrowProps> = props => {
  // start and cp1 always use x3,y3 (aux unit) so the support arrow curves toward the supported unit
  const start = getOffsetPoint(
    props.x1,
    props.y1,
    props.x3,
    props.y3,
    props.offset
  );

  const cp1 = {
    x: start.x + (props.x3 - start.x) * 0.5,
    y: start.y + (props.y3 - start.y) * 0.5,
  };

  // end, endAngle and cp2 use endControlPoint when provided (curved move) so the arrowhead
  // aligns with the move arrow's arrival angle rather than the straight aux→target line
  const ecp = props.endControlPoint ?? { x: props.x3, y: props.y3 };

  const end = getOffsetPoint(
    props.x2,
    props.y2,
    ecp.x,
    ecp.y,
    props.offset + props.arrowLength
  );

  const endAngle = Math.atan2(ecp.y - props.y2, ecp.x - props.x2);

  const cp2 = {
    x: end.x + (ecp.x - end.x) * 0.5,
    y: end.y + (ecp.y - end.y) * 0.5,
  };

  const arrowStart = {
    x: end.x - (props.lineWidth / 2) * Math.cos(endAngle + Math.PI / 2),
    y: end.y - (props.lineWidth / 2) * Math.sin(endAngle + Math.PI / 2),
  };

  const arrowEnd = {
    x: end.x + (props.lineWidth / 2) * Math.cos(endAngle + Math.PI / 2),
    y: end.y + (props.lineWidth / 2) * Math.sin(endAngle + Math.PI / 2),
  };

  const arrowBottomLeft = {
    x: end.x - props.arrowWidth * Math.cos(endAngle + Math.PI / 2),
    y: end.y - props.arrowWidth * Math.sin(endAngle + Math.PI / 2),
  };

  const arrowBottomRight = {
    x: end.x + props.arrowWidth * Math.cos(endAngle + Math.PI / 2),
    y: end.y + props.arrowWidth * Math.sin(endAngle + Math.PI / 2),
  };

  const arrowTop = {
    x: end.x - props.arrowLength * Math.cos(endAngle),
    y: end.y - props.arrowLength * Math.sin(endAngle),
  };

  const centerPoint = getBezierPoint(0.3, start, cp1, cp2, end);
  const centerAngleBezier = Math.atan2(cp2.y - cp1.y, cp2.x - cp1.x);

  return (
    <>
      <path
        d={`M ${start.x} ${start.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${end.x} ${end.y}`}
        fill={"none"}
        stroke={props.stroke}
        strokeWidth={props.lineWidth + props.strokeWidth * 2}
        strokeDasharray={
          props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
        }
      />
      <path
        d={`M ${start.x} ${start.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${end.x} ${end.y}`}
        fill={"none"}
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
      {props.onRenderCenter &&
        props.onRenderCenter(centerPoint.x, centerPoint.y, centerAngleBezier)}
    </>
  );
};

export { CurvedArrow };
