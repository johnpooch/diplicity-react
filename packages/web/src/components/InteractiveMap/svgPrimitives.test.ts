import { describe, test, expect } from "vitest";
import {
  cross,
  minus,
  octagon,
  arrow,
  curvedArrow,
  supportHoldArrow,
  convoyArrow,
  moveViaConvoyArrow,
  formatCoord,
  type ArrowOptions,
  type CurvedArrowOptions,
  type SupportHoldArrowOptions,
  type ConvoyArrowOptions,
  type MoveViaConvoyArrowOptions,
} from "./svgPrimitives";

const wrap = (markup: string): string =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\n${markup}\n</svg>`;

const CROSS_OPTS = {
  x: 50,
  y: 50,
  width: 3,
  length: 16,
  angle: 45,
  fill: "red",
  stroke: "black",
  strokeWidth: 2,
};

const MINUS_OPTS = {
  x: 50,
  y: 50,
  width: 3,
  length: 12,
  angle: 90,
  fill: "red",
  stroke: "white",
  strokeWidth: 1,
};

const OCTAGON_OPTS = {
  x: 50,
  y: 50,
  size: 24,
  fill: "transparent",
  stroke: "black",
  strokeWidth: 3,
};

const ARROW_OPTS: ArrowOptions = {
  x1: 15,
  y1: 20,
  x2: 85,
  y2: 75,
  lineWidth: 3,
  arrowWidth: 6,
  arrowLength: 8,
  offset: 10,
  fill: "#1b4f9c",
  stroke: "black",
  strokeWidth: 2.5,
};

const CURVED_ARROW_OPTS: CurvedArrowOptions = {
  x1: 15,
  y1: 20,
  x2: 85,
  y2: 30,
  x3: 50,
  y3: 85,
  offset: 10,
  fill: "#3b9c3b",
  lineWidth: 3,
  stroke: "black",
  strokeWidth: 2.5,
  arrowWidth: 6,
  arrowLength: 8,
};

describe("formatCoord", () => {
  test("rounds to two decimal places", () => {
    expect(formatCoord(1.234567)).toBe("1.23");
    expect(formatCoord(5)).toBe("5");
    expect(formatCoord(-0.001)).toBe("0");
  });
});

describe("cross", () => {
  test("rotates about its centre and draws stroke then fill lines", () => {
    const svg = cross(CROSS_OPTS);
    expect(svg).toContain('transform="rotate(45, 50, 50)"');
    expect((svg.match(/<line/g) ?? []).length).toBe(4);
  });

  test("matches the committed artifact", async () => {
    await expect(wrap(cross(CROSS_OPTS))).toMatchFileSnapshot(
      "./__artifacts__/shape-cross.svg"
    );
  });
});

describe("minus", () => {
  test("draws a single stroked and filled bar", () => {
    const svg = minus(MINUS_OPTS);
    expect(svg).toContain('transform="rotate(90, 50, 50)"');
    expect((svg.match(/<line/g) ?? []).length).toBe(2);
  });

  test("matches the committed artifact", async () => {
    await expect(wrap(minus(MINUS_OPTS))).toMatchFileSnapshot(
      "./__artifacts__/shape-minus.svg"
    );
  });
});

describe("octagon", () => {
  test("draws a polygon with eight points", () => {
    const svg = octagon(OCTAGON_OPTS);
    const points = svg.match(/points="([^"]+)"/);
    expect(points).not.toBeNull();
    expect(points![1].split(" ")).toHaveLength(8);
  });

  test("invokes renderBottomCenter with the lower-edge midpoint", () => {
    let received: { x: number; y: number } | undefined;
    const svg = octagon({
      ...OCTAGON_OPTS,
      renderBottomCenter: (x, y) => {
        received = { x, y };
        return "BOTTOM_MARKER";
      },
    });
    expect(svg).toContain("BOTTOM_MARKER");
    expect(received).toBeDefined();
  });

  test("matches the committed artifact", async () => {
    await expect(wrap(octagon(OCTAGON_OPTS))).toMatchFileSnapshot(
      "./__artifacts__/shape-octagon.svg"
    );
  });
});

describe("arrow", () => {
  test("draws a straight line and an arrowhead", () => {
    const svg = arrow(ARROW_OPTS);
    expect(svg).toContain(" L ");
    expect(svg).not.toContain(" Q ");
  });

  test("uses a quadratic curve when given a control point", () => {
    const svg = arrow({ ...ARROW_OPTS, controlPoint: { x: 30, y: 80 } });
    expect(svg).toContain(" Q ");
  });

  test("invokes renderCenter with the computed centre and angle", () => {
    let received: { x: number; y: number; angle: number } | undefined;
    const svg = arrow({
      ...ARROW_OPTS,
      renderCenter: (x, y, angle) => {
        received = { x, y, angle };
        return "CENTER_MARKER";
      },
    });
    expect(svg).toContain("CENTER_MARKER");
    expect(received).toBeDefined();
  });

  test("applies a dash pattern when given one", () => {
    const svg = arrow({ ...ARROW_OPTS, dash: { length: 4, spacing: 2 } });
    expect(svg).toContain('stroke-dasharray="4 2"');
  });

  test("matches the committed straight artifact", async () => {
    await expect(wrap(arrow(ARROW_OPTS))).toMatchFileSnapshot(
      "./__artifacts__/shape-arrow.svg"
    );
  });

  test("matches the committed curved artifact", async () => {
    await expect(
      wrap(arrow({ ...ARROW_OPTS, controlPoint: { x: 30, y: 80 } }))
    ).toMatchFileSnapshot("./__artifacts__/shape-arrow-curved.svg");
  });
});

describe("curvedArrow", () => {
  test("draws a cubic curve and an arrowhead", () => {
    const svg = curvedArrow(CURVED_ARROW_OPTS);
    expect(svg).toContain(" C ");
  });

  test("matches the committed artifact", async () => {
    await expect(wrap(curvedArrow(CURVED_ARROW_OPTS))).toMatchFileSnapshot(
      "./__artifacts__/shape-curved-arrow.svg"
    );
  });
});

const SUPPORT_HOLD_OPTS: SupportHoldArrowOptions = {
  x1: 15,
  y1: 20,
  x2: 80,
  y2: 70,
  offset: 10,
  lineWidth: 3,
  fill: "#1b4f9c",
  stroke: "black",
  strokeWidth: 2.5,
};

const CONVOY_OPTS: ConvoyArrowOptions = {
  x1: 20,
  y1: 25,
  x2: 10,
  y2: 80,
  x3: 90,
  y3: 80,
  lineWidth: 3,
  offset: 10,
  fill: "#3b9c3b",
  stroke: "black",
  strokeWidth: 2.5,
};

const MOVE_VIA_CONVOY_OPTS: MoveViaConvoyArrowOptions = {
  waypoints: [
    { x: 10, y: 80 },
    { x: 40, y: 30 },
    { x: 70, y: 30 },
    { x: 90, y: 80 },
  ],
  lineWidth: 3,
  arrowWidth: 6,
  arrowLength: 8,
  offset: 10,
  fill: "#9c1b4f",
  stroke: "black",
  strokeWidth: 2.5,
};

describe("supportHoldArrow", () => {
  test("draws a line terminating in an octagon", () => {
    const svg = supportHoldArrow(SUPPORT_HOLD_OPTS);
    expect(svg).toContain(" L ");
    expect(svg).toContain("<polygon");
  });

  test("matches the committed artifact", async () => {
    await expect(wrap(supportHoldArrow(SUPPORT_HOLD_OPTS))).toMatchFileSnapshot(
      "./__artifacts__/shape-support-hold.svg"
    );
  });
});

describe("convoyArrow", () => {
  test("draws a wavy path ending in a circle", () => {
    const svg = convoyArrow(CONVOY_OPTS);
    expect(svg).toContain(" C ");
    expect(svg).toContain('r="5"');
  });

  test("ends the wave at the attachment point when given one", () => {
    const svg = convoyArrow({
      ...CONVOY_OPTS,
      attachmentPoint: { x: 55, y: 80 },
    });
    expect(svg).toContain('cx="55" cy="80" r="5"');
  });

  test("falls back to the closest point on the army's line", () => {
    const svg = convoyArrow(CONVOY_OPTS);
    expect(svg).toContain('cx="20" cy="80" r="5"');
  });

  test("renders only the failure marker when fleet and attachment coincide", () => {
    const svg = convoyArrow({
      ...CONVOY_OPTS,
      attachmentPoint: { x: CONVOY_OPTS.x1, y: CONVOY_OPTS.y1 },
      renderCenter: () => "FAIL_MARKER",
    });
    expect(svg).toBe("<g>FAIL_MARKER</g>");
  });

  test("matches the committed artifact", async () => {
    await expect(
      wrap(convoyArrow({ ...CONVOY_OPTS, attachmentPoint: { x: 55, y: 80 } }))
    ).toMatchFileSnapshot("./__artifacts__/shape-convoy.svg");
  });
});

describe("moveViaConvoyArrow", () => {
  test("returns nothing for fewer than two waypoints", () => {
    expect(
      moveViaConvoyArrow({ ...MOVE_VIA_CONVOY_OPTS, waypoints: [{ x: 0, y: 0 }] })
    ).toBe("");
  });

  test("threads a B-spline through the waypoints with an arrowhead", () => {
    const svg = moveViaConvoyArrow(MOVE_VIA_CONVOY_OPTS);
    expect(svg).toContain(" Q ");
    expect((svg.match(/<path/g) ?? []).length).toBe(3);
  });

  test("matches the committed artifact", async () => {
    await expect(
      wrap(moveViaConvoyArrow(MOVE_VIA_CONVOY_OPTS))
    ).toMatchFileSnapshot("./__artifacts__/shape-move-via-convoy.svg");
  });
});

describe("determinism", () => {
  test("repeated calls produce identical output", () => {
    expect(arrow(ARROW_OPTS)).toBe(arrow(ARROW_OPTS));
    expect(curvedArrow(CURVED_ARROW_OPTS)).toBe(curvedArrow(CURVED_ARROW_OPTS));
    expect(octagon(OCTAGON_OPTS)).toBe(octagon(OCTAGON_OPTS));
    expect(convoyArrow(CONVOY_OPTS)).toBe(convoyArrow(CONVOY_OPTS));
    expect(moveViaConvoyArrow(MOVE_VIA_CONVOY_OPTS)).toBe(
      moveViaConvoyArrow(MOVE_VIA_CONVOY_OPTS)
    );
  });
});
