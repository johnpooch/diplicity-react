import React, { useState } from "react";
import { Arrow } from "./shapes/arrow";
import { Cross } from "./shapes/cross";
import { CurvedArrow } from "./shapes/curved-arrow";
import { Octagon } from "./shapes/octagon";
import { NationOrder, Phase, Variant } from "../../store";

import classical from "../../maps/classical.json";

const VARIANT_MAPS: Record<string, typeof classical> = {
  classical,
};

const getMap = (variant: Variant) => {
  return VARIANT_MAPS[variant.id] || VARIANT_MAPS.classical;
};

type InteractiveMapProps = {
  interactive?: boolean;
  variant: Variant;
  phase: Phase;
  orderInProgress?: {
    source?: string;
    type?: string;
    target?: string;
    aux?: string;
  };
  orders: NationOrder[] | undefined;
  onClickProvince?: (province: string) => void;
};

const HOVER_STROKE_WIDTH = 5;
const HOVER_STROKE_COLOR = "white";
const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

const SOURCE_STROKE_WIDTH = 5;
const SOURCE_STROKE_COLOR = "white";
const SOURCE_FILL = "rgba(255, 255, 255, 0.8)";

const TARGET_STROKE_WIDTH = 5;
const TARGET_STROKE_COLOR = "white";
const TARGET_FILL = "rgba(255, 255, 255, 0.8)";

const DEFAULT_FILL = "transparent";

const UNIT_RADIUS = 10;
const UNIT_OFFSET_X = 10;
const UNIT_OFFSET_Y = 10;

const ORDER_STROKE_WIDTH = 1;
const ORDER_LINE_WIDTH = 5;
const ORDER_ARROW_WIDTH = 7.5;
const ORDER_ARROW_LENGTH = 10;
const ORDER_DASH_LENGTH = 5;
const ORDER_DASH_SPACING = 2.5;

const ORDER_FAILED_CROSS_WIDTH = 4;
const ORDER_FAILED_CROSS_LENGTH = 16;
const ORDER_FAILED_CROSS_FILL = "red";
const ORDER_FAILED_CROSS_STROKE = "black";
const ORDER_FAILED_CROSS_STROKE_WIDTH = 2;

const InteractiveMap: React.FC<InteractiveMapProps> = props => {
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  const map = getMap(props.variant);

  const getFill = (provinceId: string) => {
    const isSource = props.orderInProgress?.source === provinceId;
    const isTarget = props.orderInProgress?.target === provinceId;
    const isHovered = hoveredProvince === provinceId;
    const supplyCenter = props.phase.supplyCenters.find(
      sc => sc.province.id === provinceId
    );
    if (supplyCenter) {
      const color = props.variant.nations.find(
        n => n.name === supplyCenter.nation.name
      )?.color;
      if (!color) throw new Error("Color not found");
      return color.replace(
        /rgb(a?)\((\d+), (\d+), (\d+)(, [\d.]+)?\)/,
        // "rgba($2, $3, $4, 0.4)"
        `rgba($2, $3, $4, ${isSource ? 0.3 : isHovered ? 0.4 : 0.5})`
      );
    }
    if (isSource) return SOURCE_FILL;
    if (isTarget) return TARGET_FILL;
    if (hoveredProvince === provinceId) return HOVER_FILL;
    return DEFAULT_FILL;
  };

  const getStroke = (provinceId: string) => {
    const isSource = props.orderInProgress?.source === provinceId;
    const isTarget = props.orderInProgress?.target === provinceId;
    if (isSource) return SOURCE_STROKE_COLOR;
    if (isTarget) return TARGET_STROKE_COLOR;
    if (hoveredProvince === provinceId) return HOVER_STROKE_COLOR;
    return "none";
  };

  const getStrokeWidth = (provinceId: string) => {
    const isSource = props.orderInProgress?.source === provinceId;
    const isTarget = props.orderInProgress?.target === provinceId;
    if (isSource) return SOURCE_STROKE_WIDTH;
    if (isTarget) return TARGET_STROKE_WIDTH;
    if (hoveredProvince === provinceId) return HOVER_STROKE_WIDTH;
    return 1;
  };

  return (
    <svg
      width="100%"
      height="100%"
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
      {map.provinces.map(province => {
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
              onClick={() =>
                props.interactive && props.onClickProvince?.(province.id)
              }
            />
            {province.supplyCenter && (
              <g>
                <circle
                  cx={province.supplyCenter.x}
                  cy={province.supplyCenter.y}
                  r={10}
                  fill="white"
                  stroke="black"
                  opacity={0.7}
                  strokeWidth={4}
                />
                <circle
                  cx={province.supplyCenter.x}
                  cy={province.supplyCenter.y}
                  r={5}
                  fill="none"
                  stroke="black"
                  opacity={0.7}
                  strokeWidth={4}
                />
              </g>
            )}
          </g>
        );
      })}
      {map.provinces.map(
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
      {props.phase.units.map((unit, index) => {
        const province = map.provinces.find(p => p.id === unit.province.id);
        if (!province) return null;
        const { x, y } = province.center;
        const color = props.variant.nations.find(
          n => n.name === unit.nation.name
        )?.color;
        if (!color) throw new Error("Color not found");

        return (
          <g key={`${unit.province.id}-${index}`}>
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
              y={y - 5}
              fontSize="15"
              fontWeight="bold"
              fill="black"
              textAnchor="middle"
            >
              {unit.type === "army" ? "A" : "F"}
            </text>
          </g>
        );
      })}
      {props.orders?.map(({ orders }) => {
        return orders
          .filter(o => o.orderType === "Hold")
          .map(o => {
            const source = map.provinces.find(p => p.id === o.source);
            if (!source) return null;
            return (
              <Octagon
                key={o.source}
                x={source.center.x - UNIT_OFFSET_X}
                y={source.center.y - UNIT_OFFSET_Y}
                strokeWidth={ORDER_LINE_WIDTH}
                size={24}
                stroke={"#000000"}
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
          });
      })}
      {props.orders?.map(({ nation, orders }) => {
        const color = props.variant.nations.find(n => n.name === nation)
          ?.color as string;
        return orders
          .filter(o => o.orderType === "Support")
          .map(o => {
            const source = map.provinces.find(p => p.id === o.source);
            const target = map.provinces.find(p => p.id === o.target);
            const aux = map.provinces.find(p => p.id === o.aux);
            if (!source) return null;
            if (!target) return null;
            if (!aux) return null;
            return (
              <CurvedArrow
                key={o.source}
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
                stroke={"#000000"}
                fill={color}
                dash={{
                  length: ORDER_DASH_LENGTH,
                  spacing: ORDER_DASH_SPACING,
                }}
              />
            );
          });
      })}
      {props.orders?.map(({ orders }) => {
        return orders
          .filter(o => o.orderType === "Move")
          .map(o => {
            const source = map.provinces.find(p => p.id === o.source);
            const target = map.provinces.find(p => p.id === o.target);
            if (!source) return null;
            if (!target) return null;
            return (
              <Arrow
                key={o.source}
                x1={source.center.x - UNIT_OFFSET_X}
                y1={source.center.y - UNIT_OFFSET_Y}
                x2={target.center.x - UNIT_OFFSET_X}
                y2={target.center.y - UNIT_OFFSET_Y}
                lineWidth={ORDER_LINE_WIDTH}
                arrowWidth={ORDER_ARROW_WIDTH}
                arrowLength={ORDER_ARROW_LENGTH}
                strokeWidth={ORDER_STROKE_WIDTH}
                offset={UNIT_RADIUS}
                stroke={"#000000"}
                fill={"green"}
              />
            );
          });
      })}
      {map.provinces.map(province => {
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
              onClick={() =>
                props.interactive && props.onClickProvince?.(province.id)
              }
            />
          </g>
        );
      })}
    </svg>
  );
};

export { InteractiveMap };
