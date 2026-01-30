import type { Province, Nation, Position } from "@/types/variant";
import { DraggableMarker, type MarkerType } from "./DraggableMarker";

export interface SelectedElement {
  type: MarkerType | "label";
  provinceId: string;
  labelIndex?: number;
}

interface MarkerLayerProps {
  provinces: Province[];
  nations: Nation[];
  markerType: MarkerType;
  selectedElement: SelectedElement | null;
  onMarkerClick: (provinceId: string, type: MarkerType) => void;
  onMarkerDrag: (provinceId: string, type: MarkerType, position: Position) => void;
  visible: boolean;
  svgRef: React.RefObject<SVGSVGElement | null>;
}

function getMarkerPosition(
  province: Province,
  markerType: MarkerType
): Position | null {
  switch (markerType) {
    case "unit":
      return province.unitPosition;
    case "dislodged":
      return province.dislodgedUnitPosition;
    case "supplyCenter":
      return province.supplyCenterPosition ?? null;
  }
}

function shouldShowMarker(province: Province, markerType: MarkerType): boolean {
  switch (markerType) {
    case "unit":
      return province.startingUnit !== null;
    case "dislodged":
      return province.startingUnit !== null;
    case "supplyCenter":
      return province.supplyCenter;
  }
}

function getMarkerColor(
  province: Province,
  nations: Nation[],
  markerType: MarkerType
): string {
  if (markerType === "supplyCenter") {
    if (province.homeNation) {
      const nation = nations.find((n) => n.id === province.homeNation);
      if (nation) {
        return nation.color;
      }
    }
    return "#888888";
  }

  if (province.homeNation) {
    const nation = nations.find((n) => n.id === province.homeNation);
    if (nation) {
      return nation.color;
    }
  }

  return "#666666";
}

export const MarkerLayer: React.FC<MarkerLayerProps> = ({
  provinces,
  nations,
  markerType,
  selectedElement,
  onMarkerClick,
  onMarkerDrag,
  visible,
  svgRef,
}) => {
  if (!visible) {
    return null;
  }

  return (
    <g className={`marker-layer-${markerType}`}>
      {provinces.map((province) => {
        if (!shouldShowMarker(province, markerType)) {
          return null;
        }

        const position = getMarkerPosition(province, markerType);
        if (!position) {
          return null;
        }

        const isSelected =
          selectedElement?.type === markerType &&
          selectedElement?.provinceId === province.id;

        const color = getMarkerColor(province, nations, markerType);

        return (
          <DraggableMarker
            key={`${province.id}-${markerType}`}
            x={position.x}
            y={position.y}
            color={color}
            selected={isSelected}
            markerType={markerType}
            onClick={() => onMarkerClick(province.id, markerType)}
            onDrag={(newPosition) =>
              onMarkerDrag(province.id, markerType, newPosition)
            }
            svgRef={svgRef}
          />
        );
      })}
    </g>
  );
};
