import React, { useState } from "react";
import { Map } from "../../common/map/map.parse.types";
import { MoveArrow, SupportArrow } from "./shapes/order-arrow";
import { Arrow } from "./shapes/arrow";
import { Cross } from "./shapes/cross";
import { CurvedArrow } from "./shapes/curved-arrow";
import { ParallelCurves } from "./shapes/parallel-curves";

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
const HOVER_STROKE_COLOR = "white";
const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

const SELECTED_STROKE_WIDTH = 3;
const SELECTED_STROKE_COLOR = "white";
const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";

const DEFAULT_FILL = "transparent";

const UNIT_RADIUS = 10;

const ORDER_STROKE_WIDTH = 1;
const ORDER_LINE_WIDTH = 5;
const ORDER_ARROW_WIDTH = 7.5;
const ORDER_ARROW_LENGTH = 10;
const ORDER_DASH_LENGTH = 5;
const ORDER_DASH_SPACING = 2.5;

type InteractiveMapContextType = {
  getProvince: (provinceId: string) => {
    fill: string;
    center: { x: number; y: number };
    unitCenter: { x: number; y: number };
  };
};

const InteractiveMapContext = React.createContext<
  InteractiveMapContextType | undefined
>(undefined);

const InteractiveMapContextProvider: React.FC<
  React.PropsWithChildren<InteractiveMapProps>
> = (props) => {
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  const getFill = (provinceId: string) => {
    const isSelected = selectedProvince === provinceId;
    const isHovered = hoveredProvince === provinceId;
    if (props.supplyCenters[provinceId]) {
      const color = props.nationColors[props.supplyCenters[provinceId]];
      return color.replace(
        /rgb(a?)\((\d+), (\d+), (\d+)(, [\d.]+)?\)/,
        // "rgba($2, $3, $4, 0.4)"
        `rgba($2, $3, $4, ${isSelected ? 0.3 : isHovered ? 0.4 : 0.5})`
      );
    }
    if (selectedProvince === provinceId) return SELECTED_FILL;
    if (hoveredProvince === provinceId) return HOVER_FILL;
    return DEFAULT_FILL;
  };

  const getProvince = (provinceId: string) => {
    const province = props.map.provinces.find((p) => p.id === provinceId);
    if (!province) throw new Error(`Province ${provinceId} not found`);
    return {
      fill: getFill(provinceId),
      center: province.center,
      unitCenter: { x: province.center.x - 10, y: province.center.y - 10 },
    };
  };

  return (
    <InteractiveMapContext.Provider
      value={{
        getProvince,
      }}
    >
      {props.children}
    </InteractiveMapContext.Provider>
  );
};

const useProvince = (provinceId: string) => {
  const context = React.useContext(InteractiveMapContext);
  if (!context)
    throw new Error("Must be used in InteractiveMapContextProvider");
  return context.getProvince(provinceId);
};

const Order: React.FC<{
  type: "move" | "support" | "convoy" | "hold";
  source: string;
  target: string;
  aux: string;
}> = (props) => {
  const source = useProvince(props.source);
  const target = useProvince(props.target);
  const aux = useProvince(props.aux);

  // TODO render moves after supports
  if (props.type === "move") {
    return (
      <Arrow
        x1={source.unitCenter.x}
        y1={source.unitCenter.y}
        x2={target.unitCenter.x}
        y2={target.unitCenter.y}
        lineWidth={ORDER_LINE_WIDTH}
        arrowWidth={ORDER_ARROW_WIDTH}
        arrowLength={ORDER_ARROW_LENGTH}
        strokeWidth={ORDER_STROKE_WIDTH}
        offset={UNIT_RADIUS}
        stroke={"#000000"}
        fill={"green"}
        onRenderCenter={(x, y, angle) => (
          <Cross
            x={x}
            y={y}
            width={6}
            length={16}
            angle={angle - 15}
            fill="red"
            stroke="black"
            strokeWidth={3}
          />
        )}
      />
    );
  }
  if (props.type === "support") {
    return (
      <CurvedArrow
        x1={source.unitCenter.x}
        y1={source.unitCenter.y}
        x2={target.unitCenter.x}
        y2={target.unitCenter.y}
        x3={aux.unitCenter.x}
        y3={aux.unitCenter.y}
        offset={UNIT_RADIUS}
        lineWidth={ORDER_LINE_WIDTH}
        arrowWidth={ORDER_ARROW_WIDTH}
        arrowLength={ORDER_ARROW_LENGTH}
        strokeWidth={ORDER_STROKE_WIDTH}
        stroke={"#000000"}
        fill={"green"}
        dash={{
          length: ORDER_DASH_LENGTH,
          spacing: ORDER_DASH_SPACING,
        }}
        // onRenderCenter={(x, y, angle) => (
        //   <Cross
        //     x={x}
        //     y={y}
        //     width={6}
        //     length={16}
        //     angle={angle - 15}
        //     fill="red"
        //     stroke="black"
        //     strokeWidth={3}
        //   />
        // )}
      />
    );
  }
};

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
        `rgba($2, $3, $4, ${isSelected ? 0.3 : isHovered ? 0.4 : 0.5})`
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
    <InteractiveMapContextProvider {...props}>
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
                    r={5}
                    fill="none"
                    stroke="black"
                    strokeWidth={1}
                  />
                  <circle
                    cx={province.center.x}
                    cy={province.center.y}
                    r={3}
                    fill="none"
                    stroke="black"
                    strokeWidth={1}
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
            )
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
        {Object.entries(props.orders).map(([provinceId, order]) => {
          return (
            <Order
              key={provinceId}
              type={order.type}
              source={provinceId}
              target={order.target as string}
              aux={order.aux as string}
            />
          );
        })}
      </svg>
    </InteractiveMapContextProvider>
  );
};

export { InteractiveMap };
