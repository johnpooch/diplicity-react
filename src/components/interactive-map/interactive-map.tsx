import React, { useState } from "react";
import { Map } from "../../common/map/map.parse.types";
import { Arrow } from "./shapes/arrow";
import { Cross } from "./shapes/cross";
import { CurvedArrow } from "./shapes/curved-arrow";
import { Octagon } from "./shapes/octagon";
import { HoldArrow } from "./shapes/hold-arrow";
import { ConvoyArrow } from "./shapes/convoy-arrow";

type InteractiveMapProps = {
  map: Map;
  units: {
    [provinceId: string]: { unitType: "army" | "fleet"; nation: string };
  };
  supplyCenters: {
    [provinceId: string]: string;
  };
  nationColors: { [nation: string]: string };
  orders: {
    [provinceId: string]: {
      source: string;
      type: "move" | "support" | "convoy" | "hold";
      target?: string;
      aux?: string;
      outcome?: "succeeded" | "failed";
    };
  };
};

const HOVER_STROKE_WIDTH = 3;
const HOVER_STROKE_COLOR = "black";
const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

const SELECTED_STROKE_WIDTH = 3;
const SELECTED_STROKE_COLOR = "black";
const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";

const DEFAULT_FILL = "transparent";
const SUCCESS_COLOR = "rgba(0,0,0,1)";
const FAILED_COLOR = "rgba(255,0,0,0.6)";

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
const ORDER_FAILED_CROSS_LENGTH = 20;
const ORDER_FAILED_CROSS_FILL = "red";
const ORDER_FAILED_CROSS_STROKE = "black";
const ORDER_FAILED_CROSS_STROKE_WIDTH = 2;

const InteractiveMap: React.FC<InteractiveMapProps> = (props) => {
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);

  const getFill = (provinceId: string) => {
    const isSelected = selectedProvince === provinceId;
    const isHovered = hoveredProvince === provinceId;
    if (props.supplyCenters[provinceId]) {
      const color = props.nationColors[props.supplyCenters[provinceId]];
      return color.replace(
        /rgb(a?)\((\d+), (\d+), (\d+)(, [\d.]+)?\)/,
        // "rgba($2, $3, $4, 0.4)"
        `rgba($2, $3, $4, ${isSelected ? 0.3 : isHovered ? 0.4 : 0.5})`,
      );
    }
    if (selectedProvince === provinceId) return SELECTED_FILL;
    if (hoveredProvince === provinceId) return HOVER_FILL;
    return DEFAULT_FILL;
  };

  const getStroke = (provinceId: string) => {
    if (selectedProvince === provinceId) return SELECTED_STROKE_COLOR;
    if (hoveredProvince === provinceId) return HOVER_STROKE_COLOR;
    return "none";
  };

  const getStrokeWidth = (provinceId: string) => {
    if (selectedProvince === provinceId) return SELECTED_STROKE_WIDTH;
    if (hoveredProvince === provinceId) return HOVER_STROKE_WIDTH;
    return 1;
  };

  return (
    <svg width={props.map.width} height={props.map.height}>
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
      </defs>
      {props.map.backgroundElements.map((element, index) => (
        <g key={index}>
          <path
            d={element.path}
            fill={element.styles.fill}
            stroke={element.styles.stroke}
            strokeWidth={element.styles.strokeWidth}
          />
        </g>
      ))}
      {props.map.provinces.map((province) => {
        return (
          <g key={province.id}>
            <path
              id={province.id}
              d={province.path}
              fill={getFill(province.id)}
              stroke={getStroke(province.id)}
              strokeWidth={getStrokeWidth(province.id)}
              onMouseEnter={() => setHoveredProvince(province.id)}
              onMouseLeave={() => setHoveredProvince(null)}
              onClick={() => setSelectedProvince(province.id)}
            />
            {province.supplyCenter && (
              <g>
                <circle
                  cx={province.center.x}
                  cy={province.center.y}
                  r={7}
                  fill="white"
                  stroke="black"
                  strokeWidth={2}
                />
                <circle
                  cx={province.center.x}
                  cy={province.center.y}
                  r={4}
                  fill="white"
                  stroke="black"
                  strokeWidth={2}
                />
              </g>
            )}
          </g>
        );
      })}
      {props.map.provinces.map(
        (province) =>
          province.text && (
            <text
              key={province.id}
              x={province.text.point.x + 35}
              y={province.text.point.y + 20}
              fontSize={province.text.styles.fontSize}
              fontFamily={province.text.styles.fontFamily}
              fontWeight={province.text.styles.fontWeight}
              transform={province.text.styles.transform}
            >
              {province.text.value}
            </text>
          ),
      )}
      {props.map.borders.map((element, index) => (
        <path
          key={index}
          d={element.path}
          fill="none"
          stroke="black"
          strokeWidth={1}
        />
      ))}
      {props.map.impassableProvinces.map((element, index) => (
        <path
          key={index}
          d={element.path}
          fill="url(#impassableStripes)"
          stroke="black"
          strokeWidth={1}
        />
      ))}
      {Object.entries(props.units).map(([provinceId, unit]) => {
        const province = props.map.provinces.find((p) => p.id === provinceId);
        if (!province) return null;
        const { x, y } = province.center;
        const color = props.nationColors[unit.nation];

        return (
          <g>
            <circle
              cx={x - 10}
              cy={y - 10}
              r={UNIT_RADIUS}
              fill={color}
              stroke="black"
              strokeWidth={2}
            />
            <text
              x={x - 10}
              y={y - 6}
              fontSize="12"
              fontWeight="bold"
              fill="black"
              textAnchor="middle"
            >
              {unit.unitType === "army" ? "A" : "F"}
            </text>
          </g>
        );
      })}
      {Object.entries(props.orders)
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        .filter(([_, order]) => order.type === "hold")
        .map(([provinceId, order]) => {
          const source = props.map.provinces.find((p) => p.id === provinceId);
          if (!source) return null;
          return (
            <Octagon
              x={source.center.x - UNIT_OFFSET_X}
              y={source.center.y - UNIT_OFFSET_Y}
              strokeWidth={ORDER_LINE_WIDTH}
              size={24}
              stroke={order.outcome === "failed" ? FAILED_COLOR : SUCCESS_COLOR}
              fill={"transparent"}
              onRenderBottomCenter={
                order.outcome === "failed"
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
      {Object.entries(props.orders)
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        .filter(([_, order]) => order.type === "support")
        .map(([provinceId, order]) => {
          const source = props.map.provinces.find((p) => p.id === provinceId);
          const target = props.map.provinces.find((p) => p.id === order.target);
          const unit = props.units[provinceId];
          const unitColor = unit ? props.nationColors[unit.nation] : "black"; // Default to black if no unit found
          const aux = props.map.provinces.find((p) => p.id === order.aux);
          if (!source || !target || !aux) return null;

          if (order.aux === order.target) {
            // Render HoldArrow if auxiliary is the same as the target
            return (
              <HoldArrow
                x1={source.center.x - UNIT_OFFSET_X}
                y1={source.center.y - UNIT_OFFSET_Y}
                x2={target.center.x - UNIT_OFFSET_X}
                y2={target.center.y - UNIT_OFFSET_Y}
                stroke={
                  order.outcome === "failed" ? FAILED_COLOR : SUCCESS_COLOR
                }
                fill={unitColor}
                lineWidth={ORDER_LINE_WIDTH}
                arrowWidth={ORDER_ARROW_WIDTH}
                arrowLength={ORDER_ARROW_LENGTH}
                strokeWidth={ORDER_STROKE_WIDTH}
                dash={{
                  length: ORDER_DASH_LENGTH,
                  spacing: ORDER_DASH_SPACING,
                }}
                offset={UNIT_RADIUS + UNIT_OFFSET_RADIUS}
              />
            );
          }
          return (
            <CurvedArrow
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
              stroke={order.outcome === "failed" ? FAILED_COLOR : SUCCESS_COLOR}
              fill={unitColor}
              dash={{
                length: ORDER_DASH_LENGTH,
                spacing: ORDER_DASH_SPACING,
              }}
              onRenderCenter={
                order.outcome === "failed"
                  ? (x, y, angle) => (
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

      {Object.entries(props.orders)
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        .filter(([_, order]) => order.type === "move")
        .map(([provinceId, order]) => {
          const source = props.map.provinces.find((p) => p.id === provinceId);
          const target = props.map.provinces.find((p) => p.id === order.target);
          const unit = props.units[provinceId];
          const unitColor = unit ? props.nationColors[unit.nation] : "black"; // Default to black if no unit found
          if (!source || !target) return null;
          return (
            <Arrow
              x1={source.center.x - UNIT_OFFSET_X}
              y1={source.center.y - UNIT_OFFSET_Y}
              x2={target.center.x - UNIT_OFFSET_X}
              y2={target.center.y - UNIT_OFFSET_Y}
              lineWidth={ORDER_LINE_WIDTH}
              arrowWidth={ORDER_ARROW_WIDTH}
              arrowLength={ORDER_ARROW_LENGTH}
              strokeWidth={ORDER_STROKE_WIDTH}
              offset={UNIT_RADIUS + UNIT_OFFSET_RADIUS}
              stroke={order.outcome === "failed" ? FAILED_COLOR : SUCCESS_COLOR}
              fill={unitColor}
              onRenderCenter={
                order.outcome === "failed"
                  ? (x, y, angle) => (
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
      {Object.entries(props.orders)
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        .filter(([_, order]) => order.type === "convoy")
        .map(([provinceId, order]) => {
          const source = props.map.provinces.find((p) => p.id === provinceId);
          const target = props.map.provinces.find((p) => p.id === order.target);
          const unit = props.units[provinceId];
          const unitColor = unit ? props.nationColors[unit.nation] : "black"; // Default to black if no unit found
          const aux = props.map.provinces.find((p) => p.id === order.aux);
          if (!source || !target || !aux) return null;

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
              stroke={order.outcome === "failed" ? FAILED_COLOR : SUCCESS_COLOR}
              fill={unitColor}
              dash={{
                length: ORDER_DASH_LENGTH * 2,
                spacing: ORDER_DASH_LENGTH,
              }}
              onRenderCenter={
                order.outcome === "failed"
                  ? (x, y, angle) => (
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
    </svg>
  );
};

export { InteractiveMap };
