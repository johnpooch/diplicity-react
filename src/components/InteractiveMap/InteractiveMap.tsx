import React, { useState } from "react";
import { Map } from "../../common/map/map.parse.types";

type InteractiveMapProps = {
  map: Map;
};

const HOVER_STROKE_WIDTH = 1;
const HOVER_STROKE_COLOR = "white";
const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

const SELECTED_STROKE_WIDTH = 3;
const SELECTED_STROKE_COLOR = "white";
const SELECTED_FILL = "rgba(255, 255, 255, 0.8)";

const DEFAULT_FILL = "transparent";

const InteractiveMap: React.FC<InteractiveMapProps> = ({ map }) => {
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);
  const [selectedProvince, setSelectedProvince] = useState<string | null>(null);

  const getFill = (provinceId: string) => {
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
    <svg width={map.width} height={map.height}>
      <defs>
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
            d={element.path}
            fill={element.styles.fill}
            stroke={element.styles.stroke}
            strokeWidth={element.styles.strokeWidth}
          />
        </g>
      ))}
      {map.provinces.map((province) => (
        <g key={province.id}>
          <path
            id={province.id}
            d={province.path}
            fill={province.id === "mar" ? "blue" : getFill(province.id)}
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
      ))}
      {map.provinces.map(
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
      {map.borders.map((element, index) => (
        <path
          key={index}
          d={element.path}
          fill="none"
          stroke="black"
          strokeWidth={1}
        />
      ))}
      {map.impassableProvinces.map((element, index) => (
        <path
          key={index}
          d={element.path}
          fill="url(#impassableStripes)"
          stroke="black"
          strokeWidth={1}
        />
      ))}
    </svg>
  );
};

export { InteractiveMap };
