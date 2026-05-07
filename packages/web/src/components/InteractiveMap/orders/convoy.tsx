import { getClosestPointOnLine } from "../InteractiveMap.utils";

const WAVE_AMPLITUDE = 5;
const WAVE_LENGTH = 30; // pixels per full wave
const BEZIER_K = 4 / 3; // cubic bezier factor for sine approximation

// Builds a sinusoidal path from (x1,y1) to (x2,y2).
// Always uses an even number of half-waves so the path starts and ends
// on the centre axis (zero perpendicular offset at both endpoints).
const buildWavyPath = (
  x1: number,
  y1: number,
  x2: number,
  y2: number
): string => {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len === 0) return `M ${x1} ${y1}`;

  const ux = dx / len;
  const uy = dy / len;
  // Perpendicular unit vector
  const px = -uy;
  const py = ux;

  // Round to nearest even number of half-waves (minimum 2) so both
  // endpoints always land on the centre axis.
  const rawHalfWaves = Math.round(len / (WAVE_LENGTH / 2));
  const numHalfWaves = Math.max(
    2,
    rawHalfWaves % 2 === 0 ? rawHalfWaves : rawHalfWaves + 1
  );
  const halfWaveLen = len / numHalfWaves;

  let path = `M ${x1} ${y1}`;

  for (let i = 0; i < numHalfWaves; i++) {
    const sign = i % 2 === 0 ? 1 : -1;
    const sx = x1 + i * halfWaveLen * ux;
    const sy = y1 + i * halfWaveLen * uy;
    const ex = x1 + (i + 1) * halfWaveLen * ux;
    const ey = y1 + (i + 1) * halfWaveLen * uy;

    // Control points that approximate a sine half-wave using cubic bezier
    const cp1x =
      sx + halfWaveLen * 0.25 * ux + sign * WAVE_AMPLITUDE * BEZIER_K * px;
    const cp1y =
      sy + halfWaveLen * 0.25 * uy + sign * WAVE_AMPLITUDE * BEZIER_K * py;
    const cp2x =
      ex - halfWaveLen * 0.25 * ux + sign * WAVE_AMPLITUDE * BEZIER_K * px;
    const cp2y =
      ey - halfWaveLen * 0.25 * uy + sign * WAVE_AMPLITUDE * BEZIER_K * py;

    path += ` C ${cp1x} ${cp1y} ${cp2x} ${cp2y} ${ex} ${ey}`;
  }

  return path;
};

type ConvoyArrowProps = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  x3: number;
  y3: number;
  lineWidth: number;
  arrowWidth: number;
  arrowLength: number;
  offset: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  // When provided, the fleet connects to this exact point on the rendered B-spline
  // instead of computing the closest point on the straight x2→x3 line.
  attachmentPoint?: { x: number; y: number };
  dash?: { length: number; spacing: number };
  onRenderCenter?: (x: number, y: number, angle: number) => React.ReactElement;
};

const ConvoyArrow = (props: ConvoyArrowProps) => {
  const closestPoint = props.attachmentPoint
    ? props.attachmentPoint
    : getClosestPointOnLine(
        props.x1,
        props.y1,
        props.x2,
        props.y2,
        props.x3,
        props.y3
      );

  const directionX = closestPoint.x - props.x1;
  const directionY = closestPoint.y - props.y1;
  const magnitude = Math.sqrt(
    directionX * directionX + directionY * directionY
  );

  // The attachment point is essentially at the fleet center (collinear route segment).
  // Skip the wavy line but still render the failure cross so it isn't lost.
  if (magnitude < 1) {
    if (!props.onRenderCenter) return null;
    return <g>{props.onRenderCenter(props.x1, props.y1, 0)}</g>;
  }

  const unitX = directionX / magnitude;
  const unitY = directionY / magnitude;

  const startX = props.x1 + props.offset * unitX;
  const startY = props.y1 + props.offset * unitY;
  const endX = closestPoint.x;
  const endY = closestPoint.y;

  const angle = Math.atan2(endY - startY, endX - startX);
  const centerX = (startX + endX) / 2;
  const centerY = (startY + endY) / 2;

  const wavyPath = buildWavyPath(startX, startY, endX, endY);

  return (
    <g>
      <path
        d={wavyPath}
        stroke={props.stroke}
        strokeWidth={props.lineWidth + props.strokeWidth * 2}
        fill="none"
        strokeDasharray={
          props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
        }
      />
      <path
        d={wavyPath}
        stroke={props.fill}
        strokeWidth={props.lineWidth}
        fill="none"
        strokeDasharray={
          props.dash ? `${props.dash.length} ${props.dash.spacing}` : "none"
        }
      />
      {props.onRenderCenter && props.onRenderCenter(centerX, centerY, angle)}
      <circle
        cx={endX}
        cy={endY}
        r={5}
        fill={"white"}
        stroke={"black"}
        strokeWidth={props.strokeWidth}
      />
    </g>
  );
};

export { ConvoyArrow };
