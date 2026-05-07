type MoveViaConvoyArrowProps = {
  // Full route: [source_center, ...fleet_centers_in_order, destination_center]
  waypoints: { x: number; y: number }[];
  lineWidth: number;
  arrowWidth: number;
  arrowLength: number;
  offset: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  onRenderCenter?: (x: number, y: number, angle: number) => React.ReactElement;
};

import { ROUTE_TENSION } from "../InteractiveMap.utils";

// Quadratic B-spline path through control points.
// Fleet positions are used as CONTROL POINTS (attractors), not pass-through points,
// so the curve bends toward each fleet but keeps natural clearance around its icon.
// Endpoints (source offset, destination arrowhead base) are clamped exactly.
const bSplinePath = (points: { x: number; y: number }[]): string => {
  if (points.length < 2) return "";
  if (points.length === 2)
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;

  // Midpoint between consecutive control points
  const mid = (i: number) => ({
    x: (points[i].x + points[i + 1].x) / 2,
    y: (points[i].y + points[i + 1].y) / 2,
  });

  // Scale a fleet control point toward the midpoint of its adjacent midpoints
  // to reduce how far the curve deviates toward the fleet.
  const ctrl = (i: number) => {
    const mPrev = mid(i - 1);
    const mNext = mid(i);
    const midOfMids = { x: (mPrev.x + mNext.x) / 2, y: (mPrev.y + mNext.y) / 2 };
    return {
      x: midOfMids.x + ROUTE_TENSION * (points[i].x - midOfMids.x),
      y: midOfMids.y + ROUTE_TENSION * (points[i].y - midOfMids.y),
    };
  };

  const n = points.length - 1;
  let d = `M ${points[0].x} ${points[0].y} L ${mid(0).x} ${mid(0).y}`;
  for (let i = 1; i < n; i++) {
    const c = ctrl(i);
    const m = mid(i);
    d += ` Q ${c.x} ${c.y} ${m.x} ${m.y}`;
  }
  d += ` L ${points[n].x} ${points[n].y}`;
  return d;
};

const unit = (dx: number, dy: number) => {
  const len = Math.sqrt(dx * dx + dy * dy);
  return len === 0 ? { ux: 0, uy: 0 } : { ux: dx / len, uy: dy / len };
};

const MoveViaConvoyArrow = (props: MoveViaConvoyArrowProps) => {
  const pts = props.waypoints;
  if (pts.length < 2) return null;

  // Start: offset from source center toward first fleet (or destination)
  const { ux: sux, uy: suy } = unit(pts[1].x - pts[0].x, pts[1].y - pts[0].y);
  const startPt = {
    x: pts[0].x + sux * props.offset,
    y: pts[0].y + suy * props.offset,
  };

  // End tangent: direction of last segment (second-to-last → last)
  const last = pts[pts.length - 1];
  const prev = pts[pts.length - 2];
  const { ux: eux, uy: euy } = unit(last.x - prev.x, last.y - prev.y);
  const endAngle = Math.atan2(euy, eux);

  // Arrowhead tip: offset back from destination along end tangent
  const tipX = last.x - eux * props.offset;
  const tipY = last.y - euy * props.offset;

  // Line ends at base of arrowhead
  const lineEndPt = {
    x: tipX - eux * props.arrowLength,
    y: tipY - euy * props.arrowLength,
  };

  // Build modified waypoints for the curve: replace first and last with offset points
  const curvePts = [startPt, ...pts.slice(1, -1), lineEndPt];
  const pathD = bSplinePath(curvePts);

  // Arrowhead polygon
  const perpAngle = endAngle + Math.PI / 2;
  const arrowBottomLeft = {
    x: lineEndPt.x - props.arrowWidth * Math.cos(perpAngle),
    y: lineEndPt.y - props.arrowWidth * Math.sin(perpAngle),
  };
  const arrowBottomRight = {
    x: lineEndPt.x + props.arrowWidth * Math.cos(perpAngle),
    y: lineEndPt.y + props.arrowWidth * Math.sin(perpAngle),
  };
  const arrowLineLeft = {
    x: lineEndPt.x - (props.lineWidth / 2) * Math.cos(perpAngle),
    y: lineEndPt.y - (props.lineWidth / 2) * Math.sin(perpAngle),
  };
  const arrowLineRight = {
    x: lineEndPt.x + (props.lineWidth / 2) * Math.cos(perpAngle),
    y: lineEndPt.y + (props.lineWidth / 2) * Math.sin(perpAngle),
  };

  // The B-spline passes through midpoints between consecutive control points.
  // Use the middle such midpoint as the cross position — it lies exactly on the curve.
  const mids = curvePts.slice(0, -1).map((p, i) => ({
    x: (p.x + curvePts[i + 1].x) / 2,
    y: (p.y + curvePts[i + 1].y) / 2,
  }));
  const midIdx = Math.floor(mids.length / 2);
  const centerX = mids[midIdx].x;
  const centerY = mids[midIdx].y;
  const centerAngle = Math.atan2(
    curvePts[midIdx + 1].y - curvePts[midIdx].y,
    curvePts[midIdx + 1].x - curvePts[midIdx].x
  );

  return (
    <g>
      <path
        d={pathD}
        stroke={props.stroke}
        strokeWidth={props.lineWidth + props.strokeWidth * 2}
        fill="none"
      />
      <path
        d={pathD}
        stroke={props.fill}
        strokeWidth={props.lineWidth}
        fill="none"
      />
      <path
        d={`M ${arrowLineLeft.x} ${arrowLineLeft.y} L ${arrowBottomLeft.x} ${arrowBottomLeft.y} L ${tipX} ${tipY} L ${arrowBottomRight.x} ${arrowBottomRight.y} L ${arrowLineRight.x} ${arrowLineRight.y}`}
        stroke={props.stroke}
        strokeWidth={props.strokeWidth}
        fill={props.fill}
      />
      {props.onRenderCenter &&
        props.onRenderCenter(centerX, centerY, centerAngle)}
    </g>
  );
};

export { MoveViaConvoyArrow };
