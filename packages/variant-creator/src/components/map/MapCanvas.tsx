import type { VariantDefinition } from "@/types/variant";
import { DecorativeLayer } from "@/components/map/DecorativeLayer";

interface MapCanvasProps {
  variant: VariantDefinition;
}

export const MapCanvas: React.FC<MapCanvasProps> = ({ variant }) => {
  const { dimensions, provinces, decorativeElements } = variant;

  return (
    <svg
      viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
      className="w-full h-auto border rounded-lg"
      style={{ maxHeight: "60vh" }}
    >
      <DecorativeLayer elements={decorativeElements} />

      {provinces.map(province => (
        <path
          key={province.elementId}
          d={province.path}
          fill="#C8B896"
          stroke="#333"
          strokeWidth="1"
        />
      ))}
    </svg>
  );
};
