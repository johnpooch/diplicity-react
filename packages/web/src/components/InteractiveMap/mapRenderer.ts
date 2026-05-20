import { parseDsvg, type ParsedDsvg, type Point } from "./dsvgParser";
import {
  formatCoord,
  cross,
  minus,
  octagon,
  arrow,
  curvedArrow,
  supportHoldArrow,
  convoyArrow,
  moveViaConvoyArrow,
} from "./svgPrimitives";
import {
  headToHeadControlPoint,
  staggeredSupportEnd,
  buildConvoyRoute,
  type ConvoyRoute,
} from "./orderGeometry";

export type UnitState = {
  province: string;
  nation: string;
  type: "Army" | "Fleet";
  dislodged?: boolean;
  civilDisorder?: boolean;
};

export type OrderType =
  | "Hold"
  | "Move"
  | "MoveViaConvoy"
  | "Support"
  | "Convoy"
  | "Build"
  | "Disband";

export type OrderState = {
  type: OrderType;
  nation: string;
  source: string;
  target?: string;
  aux?: string;
  unitType?: "Army" | "Fleet";
  failed?: boolean;
};

export type RenderState = {
  nationColors?: Record<string, string>;
  supplyCenters?: { province: string; nation: string }[];
  units?: UnitState[];
  orders?: OrderState[];
  selected?: string[];
  highlighted?: string[];
};

const DEFAULT_FILL = "transparent";
const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";
const SELECTED_STROKE_COLOR = "white";
const HIGHLIGHTED_STROKE_COLOR = "#FFFFFF";
const SELECTED_STROKE_WIDTH = 5;
const HIGHLIGHTED_STROKE_WIDTH = 5;
const DEFAULT_STROKE_WIDTH = 1;
const SUPPLY_CENTER_OPACITY_ACTIVE = 0.3;
const SUPPLY_CENTER_OPACITY_DEFAULT = 0.5;

const UNIT_RADIUS = 10;
const UNIT_OFFSET_RADIUS = 5;
const DISLODGED_OFFSET = 8;
const SUPPLY_CENTER_OUTER_RADIUS = 7;
const SUPPLY_CENTER_INNER_RADIUS = 4;
const DIMMED_UNIT_OPACITY = 0.7;
const GHOST_UNIT_OPACITY = 0.6;

const ORDER_LINE_WIDTH = 3;
const ORDER_ARROW_WIDTH = 6;
const ORDER_ARROW_LENGTH = 8;
const ORDER_STROKE_WIDTH = 2.5;
const ORDER_DASH = { length: 4, spacing: 2 };
const SUCCESS_COLOR = "rgba(0,0,0,1)";
const HOLD_OCTAGON_SIZE = 24;
const FAILED_CROSS_WIDTH = 3;
const FAILED_CROSS_LENGTH = 16;
const FAILED_CROSS_ANGLE = 45;
const ORDER_MARKER_WIDTH = 3;
const ORDER_MARKER_LENGTH = 12;
const ORDER_MARKER_ANGLE = 90;
const BUILD_CROSS_OFFSET_X = 8;
const BUILD_CROSS_OFFSET_Y = -8;
const DISBAND_MARKER_OFFSET_X = 10;
const DISBAND_MARKER_OFFSET_Y = -6;

const HIGHLIGHTED_STRIPES_DEFS =
  '<defs><pattern patternTransform="rotate(45)" height="8" width="8"' +
  ' patternUnits="userSpaceOnUse" id="highlightedStripes">' +
  '<line stroke-width="2" stroke-opacity="0.6" stroke="#FFFFFF"' +
  ' y2="8" x2="0" y1="0" x1="0"/></pattern></defs>';

const layer = (id: string, markup: string): string =>
  `<g id="${id}">${markup}</g>`;

const opacityAttr = (opacity: number): string =>
  opacity === 1 ? "" : ` opacity="${opacity}"`;

const nationColor = (state: RenderState, nation: string): string => {
  const color = state.nationColors?.[nation];
  if (!color) {
    throw new Error(`No colour for nation "${nation}"`);
  }
  return color;
};

const toRgba = (color: string, opacity: number): string => {
  const hex = color.match(/^#([0-9a-fA-F]{6})$/);
  if (hex) {
    const r = parseInt(hex[1].slice(0, 2), 16);
    const g = parseInt(hex[1].slice(2, 4), 16);
    const b = parseInt(hex[1].slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color.replace(
    /rgb(a?)\((\d+), (\d+), (\d+)(, [\d.]+)?\)/,
    `rgba($2, $3, $4, ${opacity})`
  );
};

type ProvinceFill = {
  fill: string;
  stroke: string;
  strokeWidth: number;
  selected: boolean;
  highlighted: boolean;
};

const provinceFill = (provinceId: string, state: RenderState): ProvinceFill => {
  const selected = state.selected?.includes(provinceId) ?? false;
  const highlighted = state.highlighted?.includes(provinceId) ?? false;
  const owner = state.supplyCenters?.find((sc) => sc.province === provinceId);

  let fill = DEFAULT_FILL;
  if (owner) {
    const opacity =
      selected || highlighted
        ? SUPPLY_CENTER_OPACITY_ACTIVE
        : SUPPLY_CENTER_OPACITY_DEFAULT;
    fill = toRgba(nationColor(state, owner.nation), opacity);
  } else if (selected) {
    fill = SELECTED_FILL;
  }

  let stroke = "none";
  if (selected) {
    stroke = SELECTED_STROKE_COLOR;
  } else if (highlighted) {
    stroke = HIGHLIGHTED_STROKE_COLOR;
  }

  const strokeWidth = selected
    ? SELECTED_STROKE_WIDTH
    : highlighted
      ? HIGHLIGHTED_STROKE_WIDTH
      : DEFAULT_STROKE_WIDTH;

  return { fill, stroke, strokeWidth, selected, highlighted };
};

const provinceFillsLayer = (
  regionPaths: Map<string, string>,
  state: RenderState
): string => {
  const parts: string[] = [];
  for (const [id, d] of regionPaths) {
    const style = provinceFill(id, state);
    if (style.fill === DEFAULT_FILL && style.stroke === "none") {
      continue;
    }
    const attributes = `d="${d}" fill="${style.fill}" stroke="${style.stroke}" stroke-width="${style.strokeWidth}"`;
    if (style.highlighted && !style.selected) {
      const values = `${HIGHLIGHTED_STROKE_WIDTH};${HIGHLIGHTED_STROKE_WIDTH + 2};${HIGHLIGHTED_STROKE_WIDTH}`;
      parts.push(
        `<path ${attributes}><animate attributeName="stroke-width" values="${values}" dur="2s" repeatCount="indefinite"/></path>`
      );
    } else {
      parts.push(`<path ${attributes}/>`);
    }
    if (style.highlighted) {
      parts.push(
        `<path d="${d}" fill="url(#highlightedStripes)" stroke="none" pointer-events="none"/>`
      );
    }
  }
  return parts.join("\n");
};

const supplyCenterMarkersLayer = (supplyCenters: Map<string, Point>): string => {
  const parts: string[] = [];
  for (const [, position] of supplyCenters) {
    const cx = formatCoord(position.x);
    const cy = formatCoord(position.y);
    parts.push(
      `<g><circle cx="${cx}" cy="${cy}" r="${SUPPLY_CENTER_OUTER_RADIUS}" fill="white" stroke="black" stroke-width="2" opacity="0.8"/>` +
        `<circle cx="${cx}" cy="${cy}" r="${SUPPLY_CENTER_INNER_RADIUS}" fill="white" stroke="black" stroke-width="2" opacity="0.8"/></g>`
    );
  }
  return parts.join("\n");
};

const retreatFlag = (cx: number, cy: number): string =>
  `<g transform="translate(${formatCoord(cx + 6)}, ${formatCoord(cy - 16)}) scale(1.5)">` +
  `<line x1="0" y1="0" x2="0" y2="12" stroke="black" stroke-width="2"/>` +
  `<path d="M 0 0 L 8 2 L 8 6 L 0 8 Z" fill="white" stroke="black" stroke-width="1"/></g>`;

const civilDisorderBadge = (cx: number, cy: number): string =>
  `<g data-civil-disorder="true" transform="translate(${formatCoord(cx - 14)}, ${formatCoord(cy - 14)})">` +
  `<circle cx="0" cy="0" r="6" fill="white" stroke="black" stroke-width="1.5"/>` +
  `<text x="0" y="3" font-size="9" font-weight="bold" fill="black" text-anchor="middle">Z</text></g>`;

const unitToken = (
  cx: number,
  cy: number,
  type: "Army" | "Fleet",
  color: string,
  circleOpacity: number,
  textOpacity: number
): string => {
  const label = type === "Army" ? "A" : "F";
  return (
    `<circle cx="${formatCoord(cx)}" cy="${formatCoord(cy)}" r="${UNIT_RADIUS}" fill="${color}" stroke="black" stroke-width="2"${opacityAttr(circleOpacity)}/>` +
    `<text x="${formatCoord(cx)}" y="${formatCoord(cy + 5)}" font-size="15" font-weight="bold" fill="black" text-anchor="middle"${opacityAttr(textOpacity)}>${label}</text>`
  );
};

const unitMarkup = (
  unit: UnitState,
  position: Point,
  color: string,
  dimmed: boolean
): string => {
  const offset = unit.dislodged ? DISLODGED_OFFSET : 0;
  const cx = position.x + offset;
  const cy = position.y + offset;
  const token = unitToken(
    cx,
    cy,
    unit.type,
    color,
    dimmed ? DIMMED_UNIT_OPACITY : 1,
    1
  );
  const flag = unit.dislodged && !dimmed ? retreatFlag(cx, cy) : "";
  const cdBadge = unit.civilDisorder && !dimmed ? civilDisorderBadge(cx, cy) : "";
  return `<g>${token}${flag}${cdBadge}</g>`;
};

const unitsLayer = (
  unitPositions: Map<string, Point>,
  state: RenderState
): string => {
  const ordered = [...(state.units ?? [])].sort(
    (a, b) => Number(a.dislodged ?? false) - Number(b.dislodged ?? false)
  );
  const disbanding = new Set(
    (state.orders ?? [])
      .filter((order) => order.type === "Disband")
      .map((order) => order.source)
  );
  const parts: string[] = [];
  for (const unit of ordered) {
    const position = unitPositions.get(unit.province);
    if (!position) {
      continue;
    }
    parts.push(
      unitMarkup(
        unit,
        position,
        nationColor(state, unit.nation),
        disbanding.has(unit.province)
      )
    );
  }
  return parts.join("\n");
};

const failureCross = (x: number, y: number): string =>
  cross({
    x,
    y,
    width: FAILED_CROSS_WIDTH,
    length: FAILED_CROSS_LENGTH,
    angle: FAILED_CROSS_ANGLE,
    fill: "red",
    stroke: "black",
    strokeWidth: 2,
  });

const holdMarkup = (order: OrderState, position: Point): string =>
  octagon({
    x: position.x,
    y: position.y,
    size: HOLD_OCTAGON_SIZE,
    fill: "transparent",
    stroke: SUCCESS_COLOR,
    strokeWidth: ORDER_LINE_WIDTH,
    renderBottomCenter: order.failed ? failureCross : undefined,
  });

const buildMarkup = (
  order: OrderState,
  position: Point,
  color: string
): string => {
  const token = unitToken(
    position.x,
    position.y,
    order.unitType ?? "Army",
    color,
    GHOST_UNIT_OPACITY,
    GHOST_UNIT_OPACITY
  );
  const marker = cross({
    x: position.x + BUILD_CROSS_OFFSET_X,
    y: position.y + BUILD_CROSS_OFFSET_Y,
    width: ORDER_MARKER_WIDTH,
    length: ORDER_MARKER_LENGTH,
    angle: ORDER_MARKER_ANGLE,
    fill: "green",
    stroke: "white",
    strokeWidth: 1,
  });
  return `<g>${token}${marker}</g>`;
};

const disbandMarkup = (position: Point): string =>
  minus({
    x: position.x + DISLODGED_OFFSET + DISBAND_MARKER_OFFSET_X,
    y: position.y + DISLODGED_OFFSET + DISBAND_MARKER_OFFSET_Y,
    width: ORDER_MARKER_WIDTH,
    length: ORDER_MARKER_LENGTH,
    angle: ORDER_MARKER_ANGLE,
    fill: "red",
    stroke: "white",
    strokeWidth: 1,
  });

const headToHeadControlPoints = (
  orders: OrderState[],
  unitPositions: Map<string, Point>
): Map<string, Point> => {
  const moves = orders.filter(
    (order) => order.type === "Move" || order.type === "MoveViaConvoy"
  );
  const moveKeys = new Set(
    moves
      .filter((order) => order.target)
      .map((order) => `${order.source}->${order.target}`)
  );
  const controlPoints = new Map<string, Point>();
  for (const order of moves) {
    if (!order.target) {
      continue;
    }
    if (!moveKeys.has(`${order.target}->${order.source}`)) {
      continue;
    }
    const source = unitPositions.get(order.source);
    const target = unitPositions.get(order.target);
    if (!source || !target) {
      continue;
    }
    controlPoints.set(
      `${order.source}->${order.target}`,
      headToHeadControlPoint(source, target)
    );
  }
  return controlPoints;
};

const supportMoveGroups = (orders: OrderState[]): Map<string, OrderState[]> => {
  const groups = new Map<string, OrderState[]>();
  for (const order of orders) {
    if (order.type !== "Support" || !order.aux || !order.target) {
      continue;
    }
    if (order.aux === order.target) {
      continue;
    }
    const key = `${order.aux}->${order.target}`;
    const group = groups.get(key);
    if (group) {
      group.push(order);
    } else {
      groups.set(key, [order]);
    }
  }
  return groups;
};

const convoyRoutes = (
  orders: OrderState[],
  unitPositions: Map<string, Point>
): Map<string, ConvoyRoute> => {
  const routes = new Map<string, ConvoyRoute>();
  const convoys = orders.filter((order) => order.type === "Convoy");
  for (const move of orders) {
    if (move.type !== "MoveViaConvoy" || !move.target) {
      continue;
    }
    const source = unitPositions.get(move.source);
    const destination = unitPositions.get(move.target);
    if (!source || !destination) {
      continue;
    }
    const fleets = convoys
      .filter(
        (convoy) => convoy.aux === move.source && convoy.target === move.target
      )
      .map((convoy) => ({
        id: convoy.source,
        point: unitPositions.get(convoy.source),
      }))
      .filter(
        (fleet): fleet is { id: string; point: Point } =>
          fleet.point !== undefined
      );
    if (fleets.length === 0) {
      continue;
    }
    routes.set(
      `${move.source}->${move.target}`,
      buildConvoyRoute(source, destination, fleets)
    );
  }
  return routes;
};

const supportOrderParts = (
  orders: OrderState[],
  unitPositions: Map<string, Point>,
  state: RenderState,
  groups: Map<string, OrderState[]>,
  headToHead: Map<string, Point>
): string[] => {
  const parts: string[] = [];
  for (const order of orders) {
    if (order.type !== "Support" || !order.target || !order.aux) {
      continue;
    }
    const source = unitPositions.get(order.source);
    const target = unitPositions.get(order.target);
    const aux = unitPositions.get(order.aux);
    if (!source || !target || !aux) {
      continue;
    }
    const color = nationColor(state, order.nation);
    const renderCenter = order.failed ? failureCross : undefined;

    if (order.aux === order.target) {
      parts.push(
        supportHoldArrow({
          x1: source.x,
          y1: source.y,
          x2: target.x,
          y2: target.y,
          offset: UNIT_RADIUS,
          endOffset: UNIT_RADIUS + UNIT_OFFSET_RADIUS,
          lineWidth: ORDER_LINE_WIDTH,
          fill: color,
          stroke: SUCCESS_COLOR,
          strokeWidth: ORDER_STROKE_WIDTH,
          dash: ORDER_DASH,
          renderCenter,
        })
      );
      continue;
    }

    const moveControlPoint = headToHead.get(`${order.aux}->${order.target}`);
    const group = groups.get(`${order.aux}->${order.target}`) ?? [];
    const end = staggeredSupportEnd(
      aux,
      target,
      group.indexOf(order),
      moveControlPoint
    );
    parts.push(
      curvedArrow({
        x1: source.x,
        y1: source.y,
        x2: end.x,
        y2: end.y,
        x3: aux.x,
        y3: aux.y,
        offset: UNIT_RADIUS,
        lineWidth: ORDER_LINE_WIDTH,
        arrowWidth: ORDER_ARROW_WIDTH,
        arrowLength: ORDER_ARROW_LENGTH,
        strokeWidth: ORDER_STROKE_WIDTH,
        stroke: SUCCESS_COLOR,
        fill: color,
        dash: ORDER_DASH,
        endControlPoint: moveControlPoint,
        renderCenter,
      })
    );
  }
  return parts;
};

const moveOrderParts = (
  orders: OrderState[],
  unitPositions: Map<string, Point>,
  state: RenderState,
  headToHead: Map<string, Point>,
  routes: Map<string, ConvoyRoute>
): string[] => {
  const parts: string[] = [];
  for (const order of orders) {
    if (order.type !== "Move" && order.type !== "MoveViaConvoy") {
      continue;
    }
    if (!order.target) {
      continue;
    }
    const source = unitPositions.get(order.source);
    const target = unitPositions.get(order.target);
    if (!source || !target) {
      continue;
    }
    const color = nationColor(state, order.nation);
    const renderCenter = order.failed ? failureCross : undefined;

    if (order.type === "MoveViaConvoy") {
      const route = routes.get(`${order.source}->${order.target}`);
      if (route) {
        parts.push(
          moveViaConvoyArrow({
            waypoints: route.waypoints,
            lineWidth: ORDER_LINE_WIDTH,
            arrowWidth: ORDER_ARROW_WIDTH,
            arrowLength: ORDER_ARROW_LENGTH,
            strokeWidth: ORDER_STROKE_WIDTH,
            offset: UNIT_RADIUS,
            stroke: SUCCESS_COLOR,
            fill: color,
            renderCenter,
          })
        );
        continue;
      }
    }
    parts.push(
      arrow({
        x1: source.x,
        y1: source.y,
        x2: target.x,
        y2: target.y,
        lineWidth: ORDER_LINE_WIDTH,
        arrowWidth: ORDER_ARROW_WIDTH,
        arrowLength: ORDER_ARROW_LENGTH,
        strokeWidth: ORDER_STROKE_WIDTH,
        offset: UNIT_RADIUS,
        stroke: SUCCESS_COLOR,
        fill: color,
        controlPoint: headToHead.get(`${order.source}->${order.target}`),
        renderCenter,
      })
    );
  }
  return parts;
};

const convoyOrderParts = (
  orders: OrderState[],
  unitPositions: Map<string, Point>,
  state: RenderState,
  routes: Map<string, ConvoyRoute>
): string[] => {
  const parts: string[] = [];
  for (const order of orders) {
    if (order.type !== "Convoy" || !order.target || !order.aux) {
      continue;
    }
    const source = unitPositions.get(order.source);
    const target = unitPositions.get(order.target);
    const aux = unitPositions.get(order.aux);
    if (!source || !target || !aux) {
      continue;
    }
    const route = routes.get(`${order.aux}->${order.target}`);
    parts.push(
      convoyArrow({
        x1: source.x,
        y1: source.y,
        x2: target.x,
        y2: target.y,
        x3: aux.x,
        y3: aux.y,
        lineWidth: ORDER_LINE_WIDTH,
        offset: UNIT_RADIUS,
        stroke: SUCCESS_COLOR,
        strokeWidth: ORDER_STROKE_WIDTH,
        fill: nationColor(state, order.nation),
        attachmentPoint: route?.attachments.get(order.source),
        renderCenter: order.failed ? failureCross : undefined,
      })
    );
  }
  return parts;
};

const ordersLayer = (
  unitPositions: Map<string, Point>,
  state: RenderState
): string => {
  const orders = state.orders ?? [];
  const ofType = (type: OrderType): OrderState[] =>
    orders.filter((order) => order.type === type);
  const headToHead = headToHeadControlPoints(orders, unitPositions);
  const groups = supportMoveGroups(orders);
  const routes = convoyRoutes(orders, unitPositions);
  const parts: string[] = [];

  for (const order of ofType("Hold")) {
    const position = unitPositions.get(order.source);
    if (position) {
      parts.push(holdMarkup(order, position));
    }
  }
  parts.push(...supportOrderParts(orders, unitPositions, state, groups, headToHead));
  parts.push(...moveOrderParts(orders, unitPositions, state, headToHead, routes));
  parts.push(...convoyOrderParts(orders, unitPositions, state, routes));
  for (const order of ofType("Build")) {
    const position = unitPositions.get(order.source);
    if (position) {
      parts.push(buildMarkup(order, position, nationColor(state, order.nation)));
    }
  }
  for (const order of ofType("Disband")) {
    const position = unitPositions.get(order.source);
    if (position) {
      parts.push(disbandMarkup(position));
    }
  }
  return parts.join("\n");
};

export class DiplicityMap {
  private readonly parsed: ParsedDsvg;

  constructor(svg: string) {
    this.parsed = parseDsvg(svg);
  }

  render(state: RenderState = {}): string {
    const { viewBox, defs, background, provinceNames, borders, foreground } =
      this.parsed;
    const viewBoxAttr = `${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`;
    const fills = provinceFillsLayer(
      new Map([
        ...this.parsed.provincePaths,
        ...this.parsed.namedCoastPaths,
      ]),
      state
    );
    const markers = supplyCenterMarkersLayer(this.parsed.supplyCenters);
    const units = unitsLayer(this.parsed.unitPositions, state);
    const orders = ordersLayer(this.parsed.unitPositions, state);

    const parts = [
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBoxAttr}">`,
      defs,
    ];
    if (fills.includes("highlightedStripes")) {
      parts.push(HIGHLIGHTED_STRIPES_DEFS);
    }
    parts.push(layer("background", background));
    if (fills) {
      parts.push(layer("province-fills", fills));
    }
    if (markers) {
      parts.push(layer("supply-center-markers", markers));
    }
    parts.push(layer("province-names", provinceNames));
    parts.push(layer("borders", borders));
    parts.push(layer("foreground", foreground));
    if (units) {
      parts.push(layer("units", units));
    }
    if (orders) {
      parts.push(layer("orders", orders));
    }
    parts.push("</svg>");
    return parts.join("\n");
  }
}
