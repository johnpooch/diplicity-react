import type { Point } from "./dsvgParser";
import { closestPointOnLine, ROUTE_TENSION } from "./orderGeometry";

export type Dash = { length: number; spacing: number };

export const formatCoord = (n: number): string =>
  String(Math.round(n * 100) / 100);

const n = formatCoord;

const dashAttr = (dash?: Dash): string =>
  ` stroke-dasharray="${dash ? `${dash.length} ${dash.spacing}` : "none"}"`;

const lineEl = (
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  stroke: string,
  strokeWidth: number
): string =>
  `<line x1="${n(x1)}" y1="${n(y1)}" x2="${n(x2)}" y2="${n(y2)}" stroke="${stroke}" stroke-width="${n(strokeWidth)}"/>`;

const strokeLine = (
  d: string,
  stroke: string,
  strokeWidth: number,
  dash?: Dash
): string =>
  `<path d="${d}" fill="none" stroke="${stroke}" stroke-width="${n(strokeWidth)}"${dashAttr(dash)}/>`;

const polygonPath = (
  points: Point[],
  fill: string,
  stroke: string,
  strokeWidth: number
): string => {
  const d = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${n(p.x)} ${n(p.y)}`)
    .join(" ");
  return `<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${n(strokeWidth)}"/>`;
};

export type CrossOptions = {
  x: number;
  y: number;
  width: number;
  length: number;
  angle: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
};

export const cross = (o: CrossOptions): string => {
  const half = o.length / 2;
  const x1 = o.x - half;
  const x2 = o.x + half;
  const y3 = o.y - half;
  const y4 = o.y + half;
  const fillX1 = x1 + o.strokeWidth;
  const fillX2 = x2 - o.strokeWidth;
  const fillY3 = y3 + o.strokeWidth;
  const fillY4 = y4 - o.strokeWidth;
  const outer = o.width + o.strokeWidth * 2;
  return (
    `<g transform="rotate(${n(o.angle)}, ${n(o.x)}, ${n(o.y)})">` +
    `<g>${lineEl(x1, o.y, x2, o.y, o.stroke, outer)}${lineEl(o.x, y3, o.x, y4, o.stroke, outer)}</g>` +
    `<g>${lineEl(fillX1, o.y, fillX2, o.y, o.fill, o.width)}${lineEl(o.x, fillY3, o.x, fillY4, o.fill, o.width)}</g>` +
    `</g>`
  );
};

export type MinusOptions = CrossOptions;

export const minus = (o: MinusOptions): string => {
  const half = o.length / 2;
  const y3 = o.y - half;
  const y4 = o.y + half;
  const fillY3 = y3 + o.strokeWidth;
  const fillY4 = y4 - o.strokeWidth;
  const outer = o.width + o.strokeWidth * 2;
  return (
    `<g transform="rotate(${n(o.angle)}, ${n(o.x)}, ${n(o.y)})">` +
    `<g>${lineEl(o.x, y3, o.x, y4, o.stroke, outer)}</g>` +
    `<g>${lineEl(o.x, fillY3, o.x, fillY4, o.fill, o.width)}</g>` +
    `</g>`
  );
};

export type OctagonOptions = {
  x: number;
  y: number;
  size: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  opacity?: number;
  renderBottomCenter?: (x: number, y: number) => string;
};

export const octagon = (o: OctagonOptions): string => {
  const step = Math.PI / 4;
  const radius = o.size / (2 * Math.sin(step));
  const points = Array.from({ length: 8 }, (_, i) => {
    const theta = step * i + Math.PI / 8;
    return {
      x: o.x + radius * Math.cos(theta),
      y: o.y + radius * Math.sin(theta),
    };
  });
  const pointsAttr = points.map((p) => `${n(p.x)},${n(p.y)}`).join(" ");
  const bottomCenterX = (points[1].x + points[2].x) / 2;
  const bottomCenterY = (points[1].y + points[2].y) / 2;
  const extra = o.renderBottomCenter
    ? o.renderBottomCenter(bottomCenterX, bottomCenterY)
    : "";
  const opacityAttr = o.opacity !== undefined ? ` opacity="${o.opacity}"` : "";
  return (
    `<g><polygon points="${pointsAttr}" fill="${o.fill}" stroke="${o.stroke}" stroke-width="${n(o.strokeWidth)}"${opacityAttr}/>` +
    `${extra}</g>`
  );
};

export type ArrowOptions = {
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
  dash?: Dash;
  controlPoint?: Point;
  renderCenter?: (x: number, y: number, angle: number) => string;
};

export const arrow = (o: ArrowOptions): string => {
  if (o.controlPoint) {
    const { x: cx, y: cy } = o.controlPoint;

    const startDx = cx - o.x1;
    const startDy = cy - o.y1;
    const startLen = Math.sqrt(startDx * startDx + startDy * startDy);
    const startX = o.x1 + (startDx / startLen) * o.offset;
    const startY = o.y1 + (startDy / startLen) * o.offset;

    const endDx = o.x2 - cx;
    const endDy = o.y2 - cy;
    const endLen = Math.sqrt(endDx * endDx + endDy * endDy);
    const etx = endDx / endLen;
    const ety = endDy / endLen;
    const endAngle = Math.atan2(ety, etx);

    const tipX = o.x2 - etx * o.offset;
    const tipY = o.y2 - ety * o.offset;
    const endX = tipX - etx * o.arrowLength;
    const endY = tipY - ety * o.arrowLength;

    const perpAngle = endAngle + Math.PI / 2;
    const perpCos = Math.cos(perpAngle);
    const perpSin = Math.sin(perpAngle);
    const arrowhead: Point[] = [
      { x: endX - (o.lineWidth / 2) * perpCos, y: endY - (o.lineWidth / 2) * perpSin },
      { x: endX - o.arrowWidth * perpCos, y: endY - o.arrowWidth * perpSin },
      { x: tipX, y: tipY },
      { x: endX + o.arrowWidth * perpCos, y: endY + o.arrowWidth * perpSin },
      { x: endX + (o.lineWidth / 2) * perpCos, y: endY + (o.lineWidth / 2) * perpSin },
    ];

    const centerX = 0.25 * o.x1 + 0.5 * cx + 0.25 * o.x2;
    const centerY = 0.25 * o.y1 + 0.5 * cy + 0.25 * o.y2;
    const centerAngle = Math.atan2(o.y2 - o.y1, o.x2 - o.x1);

    const d = `M ${n(startX)} ${n(startY)} Q ${n(cx)} ${n(cy)} ${n(endX)} ${n(endY)}`;
    return (
      `<g>` +
      strokeLine(d, o.stroke, o.lineWidth + o.strokeWidth * 2, o.dash) +
      strokeLine(d, o.fill, o.lineWidth, o.dash) +
      polygonPath(arrowhead, o.fill, o.stroke, o.strokeWidth) +
      (o.renderCenter ? o.renderCenter(centerX, centerY, centerAngle) : "") +
      `</g>`
    );
  }

  const angle = Math.atan2(o.y2 - o.y1, o.x2 - o.x1);
  const offsetX = o.offset * Math.cos(angle);
  const offsetY = o.offset * Math.sin(angle);

  const startX = o.x1 + offsetX;
  const startY = o.y1 + offsetY;
  const endX = o.x2 - offsetX - o.arrowLength * Math.cos(angle);
  const endY = o.y2 - offsetY - o.arrowLength * Math.sin(angle);

  const centerX = (startX + endX) / 2;
  const centerY = (startY + endY) / 2;

  const perpAngle = angle + Math.PI / 2;
  const perpCos = Math.cos(perpAngle);
  const perpSin = Math.sin(perpAngle);
  const arrowhead: Point[] = [
    { x: endX - (o.lineWidth / 2) * perpCos, y: endY - (o.lineWidth / 2) * perpSin },
    { x: endX - o.arrowWidth * perpCos, y: endY - o.arrowWidth * perpSin },
    { x: endX + o.arrowLength * Math.cos(angle), y: endY + o.arrowLength * Math.sin(angle) },
    { x: endX + o.arrowWidth * perpCos, y: endY + o.arrowWidth * perpSin },
    { x: endX + (o.lineWidth / 2) * perpCos, y: endY + (o.lineWidth / 2) * perpSin },
  ];

  const d = `M ${n(startX)} ${n(startY)} L ${n(endX)} ${n(endY)}`;
  return (
    `<g>` +
    strokeLine(d, o.stroke, o.lineWidth + o.strokeWidth * 2, o.dash) +
    strokeLine(d, o.fill, o.lineWidth, o.dash) +
    polygonPath(arrowhead, o.fill, o.stroke, o.strokeWidth) +
    (o.renderCenter ? o.renderCenter(centerX, centerY, angle) : "") +
    `</g>`
  );
};

const offsetPoint = (
  from: Point,
  toward: Point,
  offset: number
): Point => {
  const dx = toward.x - from.x;
  const dy = toward.y - from.y;
  const len = Math.sqrt(dx * dx + dy * dy);
  return { x: from.x + (dx / len) * offset, y: from.y + (dy / len) * offset };
};

const cubicBezierPoint = (
  t: number,
  p0: Point,
  p1: Point,
  p2: Point,
  p3: Point
): Point => {
  const mt = 1 - t;
  return {
    x:
      mt ** 3 * p0.x +
      3 * mt ** 2 * t * p1.x +
      3 * mt * t ** 2 * p2.x +
      t ** 3 * p3.x,
    y:
      mt ** 3 * p0.y +
      3 * mt ** 2 * t * p1.y +
      3 * mt * t ** 2 * p2.y +
      t ** 3 * p3.y,
  };
};

export type CurvedArrowOptions = {
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
  dash?: Dash;
  endControlPoint?: Point;
  renderCenter?: (x: number, y: number, angle: number) => string;
};

export const curvedArrow = (o: CurvedArrowOptions): string => {
  const start = offsetPoint(
    { x: o.x1, y: o.y1 },
    { x: o.x3, y: o.y3 },
    o.offset
  );
  const cp1 = {
    x: start.x + (o.x3 - start.x) * 0.5,
    y: start.y + (o.y3 - start.y) * 0.5,
  };

  const ecp = o.endControlPoint ?? { x: o.x3, y: o.y3 };
  const end = offsetPoint(
    { x: o.x2, y: o.y2 },
    ecp,
    o.offset + o.arrowLength
  );
  const endAngle = Math.atan2(ecp.y - o.y2, ecp.x - o.x2);
  const cp2 = {
    x: end.x + (ecp.x - end.x) * 0.5,
    y: end.y + (ecp.y - end.y) * 0.5,
  };

  const perpAngle = endAngle + Math.PI / 2;
  const perpCos = Math.cos(perpAngle);
  const perpSin = Math.sin(perpAngle);
  const arrowhead: Point[] = [
    { x: end.x - (o.lineWidth / 2) * perpCos, y: end.y - (o.lineWidth / 2) * perpSin },
    { x: end.x - o.arrowWidth * perpCos, y: end.y - o.arrowWidth * perpSin },
    { x: end.x - o.arrowLength * Math.cos(endAngle), y: end.y - o.arrowLength * Math.sin(endAngle) },
    { x: end.x + o.arrowWidth * perpCos, y: end.y + o.arrowWidth * perpSin },
    { x: end.x + (o.lineWidth / 2) * perpCos, y: end.y + (o.lineWidth / 2) * perpSin },
  ];

  const center = cubicBezierPoint(0.3, start, cp1, cp2, end);
  const centerAngle = Math.atan2(cp2.y - cp1.y, cp2.x - cp1.x);

  const d = `M ${n(start.x)} ${n(start.y)} C ${n(cp1.x)} ${n(cp1.y)}, ${n(cp2.x)} ${n(cp2.y)}, ${n(end.x)} ${n(end.y)}`;
  return (
    `<g>` +
    strokeLine(d, o.stroke, o.lineWidth + o.strokeWidth * 2, o.dash) +
    strokeLine(d, o.fill, o.lineWidth, o.dash) +
    polygonPath(arrowhead, o.fill, o.stroke, o.strokeWidth) +
    (o.renderCenter ? o.renderCenter(center.x, center.y, centerAngle) : "") +
    `</g>`
  );
};

export type SupportHoldArrowOptions = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  offset: number;
  endOffset?: number;
  lineWidth: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  dash?: Dash;
  renderCenter?: (x: number, y: number, angle: number) => string;
};

export const supportHoldArrow = (o: SupportHoldArrowOptions): string => {
  const angle = Math.atan2(o.y2 - o.y1, o.x2 - o.x1);
  const endOffset = o.endOffset ?? o.offset;
  const startX = o.x1 + o.offset * Math.cos(angle);
  const startY = o.y1 + o.offset * Math.sin(angle);
  const endX = o.x2 - endOffset * Math.cos(angle) - Math.cos(angle);
  const endY = o.y2 - endOffset * Math.sin(angle) - Math.sin(angle);
  const centerX = (startX + endX) / 2;
  const centerY = (startY + endY) / 2;
  const d = `M ${n(startX)} ${n(startY)} L ${n(endX)} ${n(endY)}`;
  return (
    `<g>` +
    strokeLine(d, o.stroke, o.lineWidth + o.strokeWidth * 2, o.dash) +
    strokeLine(d, o.fill, o.lineWidth, o.dash) +
    (o.renderCenter ? o.renderCenter(centerX, centerY, angle) : "") +
    octagon({
      x: endX,
      y: endY,
      size: 8,
      stroke: o.stroke,
      fill: o.fill,
      strokeWidth: 3,
    }) +
    `</g>`
  );
};

const WAVE_AMPLITUDE = 5;
const WAVE_LENGTH = 30;
const BEZIER_K = 4 / 3;

const wavyPath = (start: Point, end: Point): string => {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const length = Math.sqrt(dx * dx + dy * dy);
  if (length === 0) {
    return `M ${n(start.x)} ${n(start.y)}`;
  }
  const ux = dx / length;
  const uy = dy / length;
  const px = -uy;
  const py = ux;
  const rawHalfWaves = Math.round(length / (WAVE_LENGTH / 2));
  const halfWaves = Math.max(
    2,
    rawHalfWaves % 2 === 0 ? rawHalfWaves : rawHalfWaves + 1
  );
  const halfWaveLength = length / halfWaves;
  let d = `M ${n(start.x)} ${n(start.y)}`;
  for (let i = 0; i < halfWaves; i++) {
    const sign = i % 2 === 0 ? 1 : -1;
    const sx = start.x + i * halfWaveLength * ux;
    const sy = start.y + i * halfWaveLength * uy;
    const ex = start.x + (i + 1) * halfWaveLength * ux;
    const ey = start.y + (i + 1) * halfWaveLength * uy;
    const cp1x = sx + halfWaveLength * 0.25 * ux + sign * WAVE_AMPLITUDE * BEZIER_K * px;
    const cp1y = sy + halfWaveLength * 0.25 * uy + sign * WAVE_AMPLITUDE * BEZIER_K * py;
    const cp2x = ex - halfWaveLength * 0.25 * ux + sign * WAVE_AMPLITUDE * BEZIER_K * px;
    const cp2y = ey - halfWaveLength * 0.25 * uy + sign * WAVE_AMPLITUDE * BEZIER_K * py;
    d += ` C ${n(cp1x)} ${n(cp1y)} ${n(cp2x)} ${n(cp2y)} ${n(ex)} ${n(ey)}`;
  }
  return d;
};

export type ConvoyArrowOptions = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  x3: number;
  y3: number;
  lineWidth: number;
  offset: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  attachmentPoint?: Point;
  dash?: Dash;
  renderCenter?: (x: number, y: number, angle: number) => string;
};

export const convoyArrow = (o: ConvoyArrowOptions): string => {
  const closest =
    o.attachmentPoint ??
    closestPointOnLine(
      { x: o.x1, y: o.y1 },
      { x: o.x2, y: o.y2 },
      { x: o.x3, y: o.y3 }
    );
  const dx = closest.x - o.x1;
  const dy = closest.y - o.y1;
  const magnitude = Math.sqrt(dx * dx + dy * dy);
  if (magnitude < 1) {
    return o.renderCenter ? `<g>${o.renderCenter(o.x1, o.y1, 0)}</g>` : "";
  }
  const ux = dx / magnitude;
  const uy = dy / magnitude;
  const start = { x: o.x1 + o.offset * ux, y: o.y1 + o.offset * uy };
  const end = { x: closest.x, y: closest.y };
  const angle = Math.atan2(end.y - start.y, end.x - start.x);
  const centerX = (start.x + end.x) / 2;
  const centerY = (start.y + end.y) / 2;
  const d = wavyPath(start, end);
  return (
    `<g>` +
    strokeLine(d, o.stroke, o.lineWidth + o.strokeWidth * 2, o.dash) +
    strokeLine(d, o.fill, o.lineWidth, o.dash) +
    (o.renderCenter ? o.renderCenter(centerX, centerY, angle) : "") +
    `<circle cx="${n(end.x)}" cy="${n(end.y)}" r="5" fill="white" stroke="black" stroke-width="${n(o.strokeWidth)}"/>` +
    `</g>`
  );
};

const unitVector = (dx: number, dy: number): Point => {
  const length = Math.sqrt(dx * dx + dy * dy);
  return length === 0 ? { x: 0, y: 0 } : { x: dx / length, y: dy / length };
};

const bSplinePath = (points: Point[]): string => {
  if (points.length < 2) {
    return "";
  }
  if (points.length === 2) {
    return `M ${n(points[0].x)} ${n(points[0].y)} L ${n(points[1].x)} ${n(points[1].y)}`;
  }
  const mid = (i: number): Point => ({
    x: (points[i].x + points[i + 1].x) / 2,
    y: (points[i].y + points[i + 1].y) / 2,
  });
  const control = (i: number): Point => {
    const previous = mid(i - 1);
    const next = mid(i);
    const midOfMids = {
      x: (previous.x + next.x) / 2,
      y: (previous.y + next.y) / 2,
    };
    return {
      x: midOfMids.x + ROUTE_TENSION * (points[i].x - midOfMids.x),
      y: midOfMids.y + ROUTE_TENSION * (points[i].y - midOfMids.y),
    };
  };
  const last = points.length - 1;
  let d = `M ${n(points[0].x)} ${n(points[0].y)} L ${n(mid(0).x)} ${n(mid(0).y)}`;
  for (let i = 1; i < last; i++) {
    const c = control(i);
    const m = mid(i);
    d += ` Q ${n(c.x)} ${n(c.y)} ${n(m.x)} ${n(m.y)}`;
  }
  d += ` L ${n(points[last].x)} ${n(points[last].y)}`;
  return d;
};

export type MoveViaConvoyArrowOptions = {
  waypoints: Point[];
  lineWidth: number;
  arrowWidth: number;
  arrowLength: number;
  offset: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  renderCenter?: (x: number, y: number, angle: number) => string;
};

export const moveViaConvoyArrow = (o: MoveViaConvoyArrowOptions): string => {
  const points = o.waypoints;
  if (points.length < 2) {
    return "";
  }
  const startDirection = unitVector(
    points[1].x - points[0].x,
    points[1].y - points[0].y
  );
  const startPoint = {
    x: points[0].x + startDirection.x * o.offset,
    y: points[0].y + startDirection.y * o.offset,
  };
  const last = points[points.length - 1];
  const beforeLast = points[points.length - 2];
  const endDirection = unitVector(
    last.x - beforeLast.x,
    last.y - beforeLast.y
  );
  const endAngle = Math.atan2(endDirection.y, endDirection.x);
  const tipX = last.x - endDirection.x * o.offset;
  const tipY = last.y - endDirection.y * o.offset;
  const lineEnd = {
    x: tipX - endDirection.x * o.arrowLength,
    y: tipY - endDirection.y * o.arrowLength,
  };
  const curvePoints = [startPoint, ...points.slice(1, -1), lineEnd];
  const d = bSplinePath(curvePoints);

  const perpAngle = endAngle + Math.PI / 2;
  const perpCos = Math.cos(perpAngle);
  const perpSin = Math.sin(perpAngle);
  const arrowhead: Point[] = [
    { x: lineEnd.x - (o.lineWidth / 2) * perpCos, y: lineEnd.y - (o.lineWidth / 2) * perpSin },
    { x: lineEnd.x - o.arrowWidth * perpCos, y: lineEnd.y - o.arrowWidth * perpSin },
    { x: tipX, y: tipY },
    { x: lineEnd.x + o.arrowWidth * perpCos, y: lineEnd.y + o.arrowWidth * perpSin },
    { x: lineEnd.x + (o.lineWidth / 2) * perpCos, y: lineEnd.y + (o.lineWidth / 2) * perpSin },
  ];

  const midpoints = curvePoints.slice(0, -1).map((p, i) => ({
    x: (p.x + curvePoints[i + 1].x) / 2,
    y: (p.y + curvePoints[i + 1].y) / 2,
  }));
  const midIndex = Math.floor(midpoints.length / 2);
  const center = midpoints[midIndex];
  const centerAngle = Math.atan2(
    curvePoints[midIndex + 1].y - curvePoints[midIndex].y,
    curvePoints[midIndex + 1].x - curvePoints[midIndex].x
  );

  return (
    `<g>` +
    strokeLine(d, o.stroke, o.lineWidth + o.strokeWidth * 2) +
    strokeLine(d, o.fill, o.lineWidth) +
    polygonPath(arrowhead, o.fill, o.stroke, o.strokeWidth) +
    (o.renderCenter ? o.renderCenter(center.x, center.y, centerAngle) : "") +
    `</g>`
  );
};
