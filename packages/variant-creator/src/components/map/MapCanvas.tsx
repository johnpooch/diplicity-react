import type { VariantDefinition } from "@/types/variant";

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
      {decorativeElements.map(element => (
        <g
          key={element.id}
          dangerouslySetInnerHTML={{ __html: element.content }}
        />
      ))}

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
