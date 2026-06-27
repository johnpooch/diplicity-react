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

const tokenize = (d: string): string[] =>
  d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e-?\d+)?/g) ?? [];

const isCommand = (token: string): boolean => /^[a-zA-Z]$/.test(token);

// Flattens an SVG path description into one polygon ring per subpath (each `M`
// starts a new ring). Supports the command set found in the variant dSVG
// province paths: M/m L/l H/h V/v C/c Z/z. Cubic segments are sampled to line
// segments so the result is a set of plain polygons suitable for hit-testing.
export const flattenPath = (d: string): Point[][] => {
  const tokens = tokenize(d);
  const rings: Point[][] = [];
  let ring: Point[] = [];
  let i = 0;
  let current: Point = { x: 0, y: 0 };
  let start: Point = { x: 0, y: 0 };
  let command = "";

  const num = (): number => Number(tokens[i++]);
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
        break;
      }
      case "L": {
        current = { x: base.x + num(), y: base.y + num() };
        ring.push(current);
        break;
      }
      case "H": {
        current = { x: base.x + num(), y: current.y };
        ring.push(current);
        break;
      }
      case "V": {
        current = { x: current.x, y: base.y + num() };
        ring.push(current);
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
        break;
      }
      case "Z": {
        ring.push(start);
        current = start;
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
