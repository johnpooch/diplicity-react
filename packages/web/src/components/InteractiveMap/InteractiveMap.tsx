import React, { useState } from "react";
import { Arrow } from "./shapes/arrow";
import { Cross } from "./shapes/cross";
import { CurvedArrow } from "./shapes/curved-arrow";
import { Octagon } from "./shapes/octagon";
import { OrderRead, PhaseRead, Variant, VariantRead } from "../../store";

import classical from "../../maps/classical.json";
import { ConvoyArrow } from "./orders/convoy";
import { SupportHoldArrow } from "./orders/support-hold";

const VARIANT_MAPS: Record<string, typeof classical> = {
  classical,
};

const getMap = (variant: Variant) => {
  return VARIANT_MAPS[variant.id] || VARIANT_MAPS.classical;
};

type InteractiveMapProps = {
  interactive?: boolean;
  variant: VariantRead;
  phase: PhaseRead;
  selected: string[];
  highlighted?: string[];
  orders: OrderRead[] | undefined;
  renderableProvinces?: string[];
  onClickProvince?: (province: string, event: React.MouseEvent<SVGPathElement>) => void;
  fullscreen?: boolean;
  style?: React.CSSProperties;
};


const HOVER_STROKE_WIDTH = 5;
const HOVER_STROKE_COLOR = "white";
const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

const SELECTED_STROKE_WIDTH = 5;
const SELECTED_STROKE_COLOR = "white";
const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";

const HIGHLIGHTED_STROKE_WIDTH = 5;
const HIGHLIGHTED_STROKE_COLOR = "#FFFFFF";

const DEFAULT_FILL = "transparent";

const SUCCESS_COLOR = "rgba(0,0,0,1)";

const UNIT_RADIUS = 10;
const UNIT_OFFSET_RADIUS = 5;
const UNIT_OFFSET_X = 10;
const UNIT_OFFSET_Y = 10;

const ORDER_STROKE_WIDTH = 2.5;
const ORDER_LINE_WIDTH = 3;
const ORDER_ARROW_WIDTH = 6;
const ORDER_ARROW_LENGTH = 8;
const ORDER_DASH_LENGTH = 4;
const ORDER_DASH_SPACING = 2;

const ORDER_FAILED_CROSS_WIDTH = 3;
const ORDER_FAILED_CROSS_LENGTH = 16;
const ORDER_FAILED_CROSS_FILL = "red";
const ORDER_FAILED_CROSS_STROKE = "black";
const ORDER_FAILED_CROSS_STROKE_WIDTH = 2;

const RETREAT_FLAG_SCALE = 1.5;
const RETREAT_FLAG_OFFSET_X = -6;
const RETREAT_FLAG_OFFSET_Y = 2;
const RETREAT_FLAG_POLE_HEIGHT = 12;
const RETREAT_FLAG_POLE_STROKE_WIDTH = 2;
const RETREAT_FLAG_STROKE_WIDTH = 1;
const RETREAT_FLAG_FILL = "white";
const RETREAT_FLAG_STROKE = "black";

const BUILD_CROSS_WIDTH = 3;
const BUILD_CROSS_LENGTH = 12;
const BUILD_CROSS_FILL = "green";
const BUILD_CROSS_STROKE = "white";
const BUILD_CROSS_STROKE_WIDTH = 1;
const BUILD_CROSS_ANGLE = 90;
const BUILD_CROSS_OFFSET_X = 8;
const BUILD_CROSS_OFFSET_Y = -8;

const SUPPLY_CENTER_OUTER_RADIUS = 7;
const SUPPLY_CENTER_INNER_RADIUS = 4;
const SUPPLY_CENTER_FILL = "white";
const SUPPLY_CENTER_STROKE = "black";
const SUPPLY_CENTER_OPACITY = 0.8;
const SUPPLY_CENTER_STROKE_WIDTH = 2;

const InteractiveMap: React.FC<InteractiveMapProps> = props => {
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  const map = getMap(props.variant);

  // Determine which provinces should be rendered
  const renderableProvinces = props.renderableProvinces || map.provinces.map(p => p.id);
  const provincesToRender = map.provinces.filter(province =>
    renderableProvinces.includes(province.id)
  );

  const getFill = (provinceId: string) => {
    const isSelected = props.selected.includes(provinceId);
    const isHighlighted = props.highlighted?.includes(provinceId);
    const isHovered = hoveredProvince === provinceId;
    const supplyCenter = props.phase.supplyCenters.find(
      sc => sc.province.id === provinceId
    );

    // For supply centers with nation colors
    if (supplyCenter) {
      const color = props.variant.nations.find(
        n => n.name === supplyCenter.nation.name
      )?.color;
      if (!color) throw new Error("Color not found");

      return color.replace(
        /rgb(a?)\((\d+), (\d+), (\d+)(, [\d.]+)?\)/,
        `rgba($2, $3, $4, ${isSelected ? 0.3 : isHighlighted ? 0.3 : isHovered ? 0.4 : 0.5})`
      );
    }

    // For non-supply center provinces
    if (isSelected) return SELECTED_FILL;
    // if (isHighlighted) return HIGHLIGHTED_FILL;
    if (isHovered) return HOVER_FILL;
    return DEFAULT_FILL;
  };

  const getStroke = (provinceId: string) => {
    const isSelected = props.selected.includes(provinceId);
    const isHighlighted = props.highlighted?.includes(provinceId);
    const isHovered = hoveredProvince === provinceId;

    if (isSelected) return SELECTED_STROKE_COLOR;
    if (isHovered && isHighlighted) return HOVER_STROKE_COLOR; // White stroke when hovering highlighted
    if (isHighlighted) return HIGHLIGHTED_STROKE_COLOR;
    if (isHovered) return HOVER_STROKE_COLOR;
    return "none";
  };

  const getStrokeWidth = (provinceId: string) => {
    const isSelected = props.selected.includes(provinceId);
    const isHighlighted = props.highlighted?.includes(provinceId);
    const isHovered = hoveredProvince === provinceId;

    if (isSelected) return SELECTED_STROKE_WIDTH;
    if (isHovered && isHighlighted) return HOVER_STROKE_WIDTH; // Thick white stroke when hovering highlighted
    if (isHighlighted) return HIGHLIGHTED_STROKE_WIDTH;
    if (isHovered) return HOVER_STROKE_WIDTH;
    return 1;
  };

  const svgStyle = props.fullscreen ? {
    minWidth: "100%",
    minHeight: "100%",
    width: "auto",
    height: "auto",
    display: "block",
    ...props.style,
  } : {
    width: "100%",
    height: "100%",
    display: "block",
    ...props.style,
  };

  return (
    <svg
      style={svgStyle}
      viewBox={`0 0 ${map.width} ${map.height}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="5"
          markerHeight="3.5"
          refX="3.5"
          refY="1.75"
          orient="auto"
        >
          <polygon points="0 0, 5 1.75, 0 3.5" fill="black" />
        </marker>
        <pattern
          patternTransform="rotate(35)"
          height="16"
          width="16"
          patternUnits="userSpaceOnUse"
          id="impassableStripes"
        >
          <line
            strokeWidth="18"
            strokeOpacity="0.1"
            stroke="#000000"
            y2="16"
            x2="0"
            y="0"
            x1="0"
          />
        </pattern>
        <pattern
          patternTransform="rotate(45)"
          height="8"
          width="8"
          patternUnits="userSpaceOnUse"
          id="highlightedStripes"
        >
          <line
            strokeWidth="2"
            strokeOpacity="0.6"
            stroke="#FFFFFF"
            y2="8"
            x2="0"
            y1="0"
            x1="0"
          />
        </pattern>
      </defs>
      {map.backgroundElements.map((element, index) => (
        <g key={index}>
          <path
            d={element.d}
            fill={element.styles.fill}
            stroke={element.styles.stroke}
            strokeWidth={element.styles.strokeWidth}
          />
        </g>
      ))}
      {provincesToRender.map(province => {
        const isHighlighted = props.highlighted?.includes(province.id);
        const isHovered = hoveredProvince === province.id;
        const isSelected = props.selected.includes(province.id);

        return (
          <g key={province.id}>
            <path
              id={province.id}
              d={province.path.d}
              fill={getFill(province.id)}
              stroke={getStroke(province.id)}
              strokeWidth={getStrokeWidth(province.id)}
              onMouseEnter={() =>
                props.interactive && setHoveredProvince(province.id)
              }
              onMouseLeave={() => props.interactive && setHoveredProvince(null)}
              onClick={(event) =>
                props.interactive && props.onClickProvince?.(province.id, event)
              }
            >
              {isHighlighted && !isSelected && !isHovered && (
                <animate
                  attributeName="stroke-width"
                  values={`${HIGHLIGHTED_STROKE_WIDTH};${HIGHLIGHTED_STROKE_WIDTH + 2};${HIGHLIGHTED_STROKE_WIDTH}`}
                  dur="2s"
                  repeatCount="indefinite"
                />
              )}
            </path>
            {isHighlighted && (
              <path
                d={province.path.d}
                fill="url(#highlightedStripes)"
                stroke="none"
                pointerEvents="none"
              />
            )}
            {province.supplyCenter && (
              <g>
                <circle
                  cx={province.supplyCenter.x}
                  cy={province.supplyCenter.y}
                  r={SUPPLY_CENTER_OUTER_RADIUS}
                  fill={SUPPLY_CENTER_FILL}
                  stroke={SUPPLY_CENTER_STROKE}
                  opacity={SUPPLY_CENTER_OPACITY}
                  strokeWidth={SUPPLY_CENTER_STROKE_WIDTH}
                />
                <circle
                  cx={province.supplyCenter.x}
                  cy={province.supplyCenter.y}
                  r={SUPPLY_CENTER_INNER_RADIUS}
                  fill={SUPPLY_CENTER_FILL}
                  stroke={SUPPLY_CENTER_STROKE}
                  opacity={SUPPLY_CENTER_OPACITY}
                  strokeWidth={SUPPLY_CENTER_STROKE_WIDTH}
                />
              </g>
            )}
          </g>
        );
      })}
      {provincesToRender.map(
        province =>
          province.text &&
          province.text.map((text, index) => (
            <text
              key={`${province.id}-${index}`}
              x={text.point.x}
              y={text.point.y}
              style={text.styles}
              fontSize={text.styles.fontSize}
              transform={text.transform}
            >
              {text.value}
            </text>
          ))
      )}
      {map.borders.map((element, index) => (
        <path
          key={`${element.id}-${index}`}
          d={element.d}
          fill="none"
          stroke="black"
          strokeWidth={1}
        />
      ))}
      {map.impassableProvinces.map((element, index) => (
        <path
          key={`${element.id}-${index}`}
          d={element.d}
          fill="url(#impassableStripes)"
          stroke="black"
          strokeWidth={1}
        />
      ))}
      {[...props.phase.units]
        .sort((a, b) => {
          // Sort so dislodged units are rendered last (on top)
          if (a.dislodgedBy && !b.dislodgedBy) return 1;
          if (!a.dislodgedBy && b.dislodgedBy) return -1;
          return 0;
        })
        .map((unit, index) => {
          const province = map.provinces.find(p => p.id === unit.province.id);
          if (!province) return null;
          const { x, y } = province.center;
          const color = props.variant.nations.find(
            n => n.name === unit.nation.name
          )?.color;
          if (!color) throw new Error("Color not found");

          // Offset dislodged units by a few pixels
          const offsetX = unit.dislodgedBy ? 8 : 0;
          const offsetY = unit.dislodgedBy ? 8 : 0;

          return (
            <g key={`${unit.province.id}-${index}`}>
              <circle
                cx={x - 10 + offsetX}
                cy={y - 10 + offsetY}
                r={UNIT_RADIUS}
                fill={color}
                stroke="black"
                strokeWidth={2}
              />
              <text
                x={x - 10 + offsetX}
                y={y - 5 + offsetY}
                fontSize="15"
                fontWeight="bold"
                fill="black"
                textAnchor="middle"
              >
                {unit.type === "Army" ? "A" : "F"}
              </text>
              {unit.dislodgedBy && (
                <g transform={`translate(${x - 8 + offsetX + UNIT_RADIUS + RETREAT_FLAG_OFFSET_X}, ${y - 18 + offsetY - UNIT_RADIUS + RETREAT_FLAG_OFFSET_Y}) scale(${RETREAT_FLAG_SCALE})`}>
                  {/* Flag pole */}
                  <line
                    x1="0"
                    y1="0"
                    x2="0"
                    y2={RETREAT_FLAG_POLE_HEIGHT}
                    stroke={RETREAT_FLAG_STROKE}
                    strokeWidth={RETREAT_FLAG_POLE_STROKE_WIDTH}
                  />
                  {/* Flag */}
                  <path
                    d="M 0 0 L 8 2 L 8 6 L 0 8 Z"
                    fill={RETREAT_FLAG_FILL}
                    stroke={RETREAT_FLAG_STROKE}
                    strokeWidth={RETREAT_FLAG_STROKE_WIDTH}
                  />
                </g>
              )}
            </g>
          );
        })}
      {props.orders?.filter(o => o.orderType === "Hold").map((o) => {
        const source = o.namedCoast ? map.provinces.find(p => p.id === o.namedCoast.id) : map.provinces.find(p => p.id === o.source.id);
        if (!source) return null;
        return (
          <Octagon
            key={o.source.id}
            x={source.center.x - UNIT_OFFSET_X}
            y={source.center.y - UNIT_OFFSET_Y}
            strokeWidth={ORDER_LINE_WIDTH}
            size={24}
            stroke={SUCCESS_COLOR}
            fill={"transparent"}
            onRenderBottomCenter={
              o.resolution && o.resolution.status !== "Succeeded"
                ? (x, y) => (
                  <Cross
                    x={x}
                    y={y}
                    width={ORDER_FAILED_CROSS_WIDTH}
                    length={ORDER_FAILED_CROSS_LENGTH}
                    angle={45}
                    fill={ORDER_FAILED_CROSS_FILL}
                    stroke={ORDER_FAILED_CROSS_STROKE}
                    strokeWidth={ORDER_FAILED_CROSS_STROKE_WIDTH}
                  />
                )
                : undefined
            }
          />
        );
      })}
      {props.orders?.filter(o => o.orderType === "Support").map((o) => {
        const color = props.variant.nations.find(n => n.name === o.nation.name)
          ?.color as string;
        const source = map.provinces.find(p => p.id === o.source.id);
        const target = map.provinces.find(p => p.id === o.target?.id);
        const aux = map.provinces.find(p => p.id === o.aux?.id);
        if (!source) return null;
        if (!target) return null;
        if (!aux) return null;

        if (aux === target) {
          // Render HoldArrow if auxiliary is the same as the target
          return (
            <SupportHoldArrow
              x1={source.center.x - UNIT_OFFSET_X}
              y1={source.center.y - UNIT_OFFSET_Y}
              x2={target.center.x - UNIT_OFFSET_X}
              y2={target.center.y - UNIT_OFFSET_Y}
              stroke={
                SUCCESS_COLOR
              }
              fill={color}
              lineWidth={ORDER_LINE_WIDTH}
              arrowWidth={ORDER_ARROW_WIDTH}
              arrowLength={ORDER_ARROW_LENGTH}
              strokeWidth={ORDER_STROKE_WIDTH}
              dash={{
                length: ORDER_DASH_LENGTH,
                spacing: ORDER_DASH_SPACING,
              }}
              offset={UNIT_RADIUS + UNIT_OFFSET_RADIUS}
              onRenderCenter={
                o.resolution && o.resolution.status !== "Succeeded"
                  ? (x: number, y: number, _angle: number) => (
                    <Cross
                      x={x}
                      y={y}
                      width={ORDER_FAILED_CROSS_WIDTH}
                      length={ORDER_FAILED_CROSS_LENGTH}
                      angle={45}
                      fill={ORDER_FAILED_CROSS_FILL}
                      stroke={ORDER_FAILED_CROSS_STROKE}
                      strokeWidth={ORDER_FAILED_CROSS_STROKE_WIDTH}
                    />
                  )
                  : undefined
              }
            />
          );
        }

        return (
          <CurvedArrow
            key={o.source.id}
            x1={source.center.x - UNIT_OFFSET_X}
            y1={source.center.y - UNIT_OFFSET_Y}
            x2={target.center.x - UNIT_OFFSET_X}
            y2={target.center.y - UNIT_OFFSET_Y}
            x3={aux.center.x - UNIT_OFFSET_X}
            y3={aux.center.y - UNIT_OFFSET_Y}
            lineWidth={ORDER_LINE_WIDTH}
            arrowWidth={ORDER_ARROW_WIDTH}
            arrowLength={ORDER_ARROW_LENGTH}
            strokeWidth={ORDER_STROKE_WIDTH}
            offset={UNIT_RADIUS}
            stroke={SUCCESS_COLOR}
            fill={color}
            dash={{
              length: ORDER_DASH_LENGTH,
              spacing: ORDER_DASH_SPACING,
            }}
            onRenderCenter={
              o.resolution && o.resolution.status !== "Succeeded"
                ? (x: number, y: number, _angle: number) => (
                  <Cross
                    x={x}
                    y={y}
                    width={ORDER_FAILED_CROSS_WIDTH}
                    length={ORDER_FAILED_CROSS_LENGTH}
                    angle={45}
                    fill={ORDER_FAILED_CROSS_FILL}
                    stroke={ORDER_FAILED_CROSS_STROKE}
                    strokeWidth={ORDER_FAILED_CROSS_STROKE_WIDTH}
                  />
                )
                : undefined
            }
          />
        );
      })}
      {props.orders?.filter(o => o.orderType === "Move" || o.orderType === "MoveViaConvoy").map((o) => {
        const source = map.provinces.find(p => p.id === o.source.id);
        const target = map.provinces.find(p => p.id === o.target?.id);
        if (!source) return null;
        if (!target) return null;
        const color = props.variant.nations.find(n => n.name === o.nation.name)
          ?.color as string;
        return (
          <Arrow
            key={o.source.id}
            x1={source.center.x - UNIT_OFFSET_X}
            y1={source.center.y - UNIT_OFFSET_Y}
            x2={target.center.x - UNIT_OFFSET_X}
            y2={target.center.y - UNIT_OFFSET_Y}
            lineWidth={ORDER_LINE_WIDTH}
            arrowWidth={ORDER_ARROW_WIDTH}
            arrowLength={ORDER_ARROW_LENGTH}
            strokeWidth={ORDER_STROKE_WIDTH}
            offset={UNIT_RADIUS}
            stroke={SUCCESS_COLOR}
            fill={color}
            onRenderCenter={
              o.resolution && o.resolution.status !== "Succeeded"
                ? (x: number, y: number, _angle: number) => (
                  <Cross
                    x={x}
                    y={y}
                    width={ORDER_FAILED_CROSS_WIDTH}
                    length={ORDER_FAILED_CROSS_LENGTH}
                    angle={45}
                    fill={ORDER_FAILED_CROSS_FILL}
                    stroke={ORDER_FAILED_CROSS_STROKE}
                    strokeWidth={ORDER_FAILED_CROSS_STROKE_WIDTH}
                  />
                )
                : undefined
            }
          />
        );
      })}
      {props.orders?.filter(o => o.orderType === "Convoy").map((o) => {
        const source = map.provinces.find(p => p.id === o.source.id);
        const target = map.provinces.find(p => p.id === o.target?.id);
        const aux = map.provinces.find(p => p.id === o.aux?.id);
        if (!source) return null;
        if (!target) return null;
        if (!aux) return null;

        const color = props.variant.nations.find(n => n.name === o.nation.name)?.color as string;

        return (
          <ConvoyArrow
            x1={source.center.x - UNIT_OFFSET_X}
            y1={source.center.y - UNIT_OFFSET_Y}
            x2={target.center.x - UNIT_OFFSET_X}
            y2={target.center.y - UNIT_OFFSET_Y}
            x3={aux.center.x - UNIT_OFFSET_X}
            y3={aux.center.y - UNIT_OFFSET_Y}
            lineWidth={ORDER_LINE_WIDTH}
            arrowWidth={ORDER_ARROW_WIDTH}
            arrowLength={ORDER_ARROW_LENGTH}
            strokeWidth={ORDER_STROKE_WIDTH}
            offset={UNIT_RADIUS + UNIT_OFFSET_RADIUS}
            stroke={SUCCESS_COLOR}
            fill={color}
            dash={{
              length: ORDER_DASH_LENGTH * 2,
              spacing: ORDER_DASH_LENGTH,
            }}
            onRenderCenter={
              o.resolution && o.resolution.status !== "Succeeded"
                ? (x: number, y: number, _angle: number) => (
                  <Cross
                    x={x}
                    y={y}
                    width={ORDER_FAILED_CROSS_WIDTH}
                    length={ORDER_FAILED_CROSS_LENGTH}
                    angle={45}
                    fill={ORDER_FAILED_CROSS_FILL}
                    stroke={ORDER_FAILED_CROSS_STROKE}
                    strokeWidth={ORDER_FAILED_CROSS_STROKE_WIDTH}
                  />
                )
                : undefined
            }
          />
        );
      })}
      {props.orders?.filter(o => o.orderType === "Build").map((o) => {
        const color = props.variant.nations.find(n => n.name === o.nation.name)
          ?.color as string;
        const source = o.namedCoast ? map.provinces.find(p => p.id === o.namedCoast.id) : map.provinces.find(p => p.id === o.source.id);
        if (!source) return null;
        const { x, y } = source.center;

        return (
          <g key={`build-${o.source.id}`}>
            <circle
              cx={x - 10}
              cy={y - 10}
              r={UNIT_RADIUS}
              fill={color}
              stroke="black"
              strokeWidth={2}
              opacity={0.6}
            />
            <text
              x={x - 10}
              y={y - 5}
              fontSize="15"
              fontWeight="bold"
              fill="black"
              textAnchor="middle"
              opacity={0.6}
            >
              {o.unitType === "Army" ? "A" : "F"}
            </text>
            <Cross
              x={x - 10 + BUILD_CROSS_OFFSET_X}
              y={y - 10 + BUILD_CROSS_OFFSET_Y}
              width={BUILD_CROSS_WIDTH}
              length={BUILD_CROSS_LENGTH}
              angle={BUILD_CROSS_ANGLE}
              fill={BUILD_CROSS_FILL}
              stroke={BUILD_CROSS_STROKE}
              strokeWidth={BUILD_CROSS_STROKE_WIDTH}
            />
          </g>
        );
      })}
      {provincesToRender.map(province => {
        return (
          <g key={province.id}>
            <path
              id={province.id}
              d={province.path.d}
              fill={"transparent"}
              onMouseEnter={() =>
                props.interactive && setHoveredProvince(province.id)
              }
              onMouseLeave={() => props.interactive && setHoveredProvince(null)}
              onClick={(event) =>
                props.interactive && props.onClickProvince?.(province.id, event)
              }
            />
          </g>
        );
      })}
    </svg>
  );
};

export { InteractiveMap };
