import type { Point } from "../InteractiveMap/dsvgParser";

const CUBIC_SAMPLES = 12;

const cubicPoint = (
  t: number,
  p0: Point,
  p1: Point,
  p2: Point,
  p3: Point
): Point => {
  const mt = 1 - t;
  return {
    x: mt ** 3 * p0.x + 3 * mt ** 2 * t * p1.x + 3 * mt * t ** 2 * p2.x + t ** 3 * p3.x,
    y: mt ** 3 * p0.y + 3 * mt ** 2 * t * p1.y + 3 * mt * t ** 2 * p2.y + t ** 3 * p3.y,
  };
};

const quadraticPoint = (t: number, p0: Point, p1: Point, p2: Point): Point => {
  const mt = 1 - t;
  return {
    x: mt ** 2 * p0.x + 2 * mt * t * p1.x + t ** 2 * p2.x,
    y: mt ** 2 * p0.y + 2 * mt * t * p1.y + t ** 2 * p2.y,
  };
};

// The implied first control point of a smooth curve: the previous control
// point mirrored about the current point, or the current point itself when the
// preceding command was not a curve of the same degree.
const smoothControl = (previous: Point | null, current: Point): Point =>
  previous
    ? { x: 2 * current.x - previous.x, y: 2 * current.y - previous.y }
    : current;

const angleBetween = (ux: number, uy: number, vx: number, vy: number): number => {
  const sign = ux * vy - uy * vx < 0 ? -1 : 1;
  const cosine = (ux * vx + uy * vy) / (Math.hypot(ux, uy) * Math.hypot(vx, vy));
  return sign * Math.acos(Math.min(1, Math.max(-1, cosine)));
};

// Endpoint-to-centre parameterisation of an elliptical arc, per SVG 1.1
// appendix F.6.5, sampled to line segments. Out-of-range radii are scaled up as
// F.6.6 requires, and a degenerate radius degrades to a straight line.
const arcPoints = (
  from: Point,
  radii: Point,
  rotation: number,
  largeArc: boolean,
  sweep: boolean,
  to: Point
): Point[] => {
  if (from.x === to.x && from.y === to.y) {
    return [];
  }
  let rx = Math.abs(radii.x);
  let ry = Math.abs(radii.y);
  if (rx === 0 || ry === 0) {
    return [to];
  }

  const phi = (rotation * Math.PI) / 180;
  const cosPhi = Math.cos(phi);
  const sinPhi = Math.sin(phi);
  const midX = (from.x - to.x) / 2;
  const midY = (from.y - to.y) / 2;
  const x1 = cosPhi * midX + sinPhi * midY;
  const y1 = -sinPhi * midX + cosPhi * midY;

  const lambda = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry);
  if (lambda > 1) {
    const scale = Math.sqrt(lambda);
    rx *= scale;
    ry *= scale;
  }

  const numerator =
    rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1;
  const denominator = rx * rx * y1 * y1 + ry * ry * x1 * x1;
  const factor =
    (largeArc === sweep ? -1 : 1) *
    Math.sqrt(Math.max(0, numerator / denominator));
  const cx1 = (factor * rx * y1) / ry;
  const cy1 = (-factor * ry * x1) / rx;
  const cx = cosPhi * cx1 - sinPhi * cy1 + (from.x + to.x) / 2;
  const cy = sinPhi * cx1 + cosPhi * cy1 + (from.y + to.y) / 2;

  const startX = (x1 - cx1) / rx;
  const startY = (y1 - cy1) / ry;
  const endX = (-x1 - cx1) / rx;
  const endY = (-y1 - cy1) / ry;
  const theta = angleBetween(1, 0, startX, startY);
  let delta = angleBetween(startX, startY, endX, endY);
  if (!sweep && delta > 0) {
    delta -= 2 * Math.PI;
  } else if (sweep && delta < 0) {
    delta += 2 * Math.PI;
  }

  const samples = Math.max(
    2,
    Math.ceil((Math.abs(delta) / (Math.PI / 2)) * CUBIC_SAMPLES)
  );
  const points: Point[] = [];
  for (let s = 1; s < samples; s++) {
    const t = theta + (delta * s) / samples;
    points.push({
      x: cx + cosPhi * rx * Math.cos(t) - sinPhi * ry * Math.sin(t),
      y: cy + sinPhi * rx * Math.cos(t) + cosPhi * ry * Math.sin(t),
    });
  }
  points.push(to);
  return points;
};

const tokenize = (d: string): string[] =>
  d.match(/[a-zA-Z]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?/g) ?? [];

const isCommand = (token: string): boolean => /^[a-zA-Z]$/.test(token);

// Flattens an SVG path description into one polygon ring per subpath (each `M`
// starts a new ring). Supports the whole path grammar — M/L/H/V/C/S/Q/T/A/Z in
// both absolute and relative form — because variant dSVGs are authored in
// arbitrary vector editors, and a skipped segment leaves `current` stale, which
// displaces every later relative segment in the ring. Curves and arcs are
// sampled to line segments so the result is a set of plain polygons suitable
// for hit-testing.
export const flattenPath = (d: string): Point[][] => {
  const tokens = tokenize(d);
  const rings: Point[][] = [];
  let ring: Point[] = [];
  let i = 0;
  let current: Point = { x: 0, y: 0 };
  let start: Point = { x: 0, y: 0 };
  let command = "";
  let cubicControl: Point | null = null;
  let quadraticControl: Point | null = null;

  const num = (): number => Number(tokens[i++]);
  // Arc flags may be packed against the following number ("0150" is 0, 1, 50),
  // so a flag consumes one digit rather than a whole token.
  const flag = (): boolean => {
    const token = tokens[i];
    if (token === undefined) {
      return false;
    }
    if (token.length > 1) {
      tokens[i] = token.slice(1);
      return token[0] === "1";
    }
    i++;
    return token === "1";
  };
  const pushRing = (): void => {
    if (ring.length > 0) {
      rings.push(ring);
    }
    ring = [];
  };

  while (i < tokens.length) {
    if (isCommand(tokens[i])) {
      command = tokens[i++];
    }
    const relative = command === command.toLowerCase();
    const base = relative ? current : { x: 0, y: 0 };

    switch (command.toUpperCase()) {
      case "M": {
        pushRing();
        current = { x: base.x + num(), y: base.y + num() };
        start = current;
        ring.push(current);
        command = relative ? "l" : "L";
        cubicControl = null;
        quadraticControl = null;
        break;
      }
      case "L": {
        current = { x: base.x + num(), y: base.y + num() };
        ring.push(current);
        cubicControl = null;
        quadraticControl = null;
        break;
      }
      case "H": {
        current = { x: base.x + num(), y: current.y };
        ring.push(current);
        cubicControl = null;
        quadraticControl = null;
        break;
      }
      case "V": {
        current = { x: current.x, y: base.y + num() };
        ring.push(current);
        cubicControl = null;
        quadraticControl = null;
        break;
      }
      case "C": {
        const c1 = { x: base.x + num(), y: base.y + num() };
        const c2 = { x: base.x + num(), y: base.y + num() };
        const end = { x: base.x + num(), y: base.y + num() };
        for (let s = 1; s <= CUBIC_SAMPLES; s++) {
          ring.push(cubicPoint(s / CUBIC_SAMPLES, current, c1, c2, end));
        }
        current = end;
        cubicControl = c2;
        quadraticControl = null;
        break;
      }
      case "S": {
        const c1 = smoothControl(cubicControl, current);
        const c2 = { x: base.x + num(), y: base.y + num() };
        const end = { x: base.x + num(), y: base.y + num() };
        for (let s = 1; s <= CUBIC_SAMPLES; s++) {
          ring.push(cubicPoint(s / CUBIC_SAMPLES, current, c1, c2, end));
        }
        current = end;
        cubicControl = c2;
        quadraticControl = null;
        break;
      }
      case "Q": {
        const c = { x: base.x + num(), y: base.y + num() };
        const end = { x: base.x + num(), y: base.y + num() };
        for (let s = 1; s <= CUBIC_SAMPLES; s++) {
          ring.push(quadraticPoint(s / CUBIC_SAMPLES, current, c, end));
        }
        current = end;
        cubicControl = null;
        quadraticControl = c;
        break;
      }
      case "T": {
        const c = smoothControl(quadraticControl, current);
        const end = { x: base.x + num(), y: base.y + num() };
        for (let s = 1; s <= CUBIC_SAMPLES; s++) {
          ring.push(quadraticPoint(s / CUBIC_SAMPLES, current, c, end));
        }
        current = end;
        cubicControl = null;
        quadraticControl = c;
        break;
      }
      case "A": {
        const radii = { x: num(), y: num() };
        const rotation = num();
        const largeArc = flag();
        const sweep = flag();
        const end = { x: base.x + num(), y: base.y + num() };
        for (const point of arcPoints(
          current,
          radii,
          rotation,
          largeArc,
          sweep,
          end
        )) {
          ring.push(point);
        }
        current = end;
        cubicControl = null;
        quadraticControl = null;
        break;
      }
      case "Z": {
        ring.push(start);
        current = start;
        cubicControl = null;
        quadraticControl = null;
        // Clearing the command stops a stray coordinate after `Z` from looping
        // forever on a case that consumes no tokens.
        command = "";
        break;
      }
      default: {
        i++;
      }
    }
  }

  pushRing();
  return rings;
};
