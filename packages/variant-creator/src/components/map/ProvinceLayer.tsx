import type { Province, Nation } from "@/types/variant";

interface ProvinceLayerProps {
  provinces: Province[];
  nations: Nation[];
  selectedProvinceId: string | null;
  hoveredProvinceId: string | null;
  adjacentProvinceIds?: string[];
  onProvinceClick?: (provinceId: string) => void;
  onProvinceMouseEnter?: (provinceId: string) => void;
  onProvinceMouseLeave?: () => void;
}

function getProvinceFill(
  province: Province,
  nations: Nation[],
  isSelected: boolean,
  isHovered: boolean,
  isAdjacent: boolean
): string {
  if (isSelected) {
    return "#FFD700";
  }

  if (isAdjacent) {
    return "#90EE90";
  }

  if (isHovered) {
    return "#E8E8E8";
  }

  if (province.type === "sea") {
    return "#8BA5D0";
  }

  if (province.homeNation) {
    const nation = nations.find((n) => n.id === province.homeNation);
    if (nation) {
      return nation.color + "80";
    }
  }

  return "#C8B896";
}

export const ProvinceLayer: React.FC<ProvinceLayerProps> = ({
  provinces,
  nations,
  selectedProvinceId,
  hoveredProvinceId,
  adjacentProvinceIds = [],
  onProvinceClick,
  onProvinceMouseEnter,
  onProvinceMouseLeave,
}) => {
  return (
    <g className="province-layer">
      {provinces.map((province) => {
        const isSelected = province.id === selectedProvinceId;
        const isHovered = province.id === hoveredProvinceId;
        const isAdjacent = adjacentProvinceIds.includes(province.id);
        const fill = getProvinceFill(
          province,
          nations,
          isSelected,
          isHovered,
          isAdjacent
        );

        return (
          <path
            key={province.elementId}
            d={province.path}
            fill={fill}
            stroke={isSelected ? "#B8860B" : "#333"}
            strokeWidth={isSelected ? 2 : 1}
            style={{ cursor: onProvinceClick ? "pointer" : "default" }}
            onClick={() => onProvinceClick?.(province.id)}
            onMouseEnter={() => onProvinceMouseEnter?.(province.id)}
            onMouseLeave={() => onProvinceMouseLeave?.()}
          />
        );
      })}
    </g>
  );
};
