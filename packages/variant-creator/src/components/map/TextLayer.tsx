import type { TextElement } from "@/types/variant";

interface TextLayerProps {
  textElements: TextElement[];
  associations: Map<number, string | null>;
  selectedTextIndex: number | null;
  onTextClick?: (textIndex: number) => void;
  onTextMouseEnter?: (textIndex: number) => void;
  onTextMouseLeave?: () => void;
}

function getTextFill(
  isSelected: boolean,
  isAssociated: boolean,
  originalFill?: string
): string {
  if (isSelected) {
    return "#FFD700";
  }

  if (!isAssociated) {
    return "#DC2626";
  }

  return originalFill ?? "#333333";
}

export const TextLayer: React.FC<TextLayerProps> = ({
  textElements,
  associations,
  selectedTextIndex,
  onTextClick,
  onTextMouseEnter,
  onTextMouseLeave,
}) => {
  return (
    <g className="text-layer">
      {textElements.map((text, index) => {
        const isSelected = index === selectedTextIndex;
        const isAssociated = associations.get(index) !== null;
        const fill = getTextFill(isSelected, isAssociated, text.styles?.fill);

        const transform = text.rotation
          ? `rotate(${text.rotation}, ${text.x}, ${text.y})`
          : undefined;

        return (
          <text
            key={index}
            x={text.x}
            y={text.y}
            transform={transform}
            fill={fill}
            fontSize={text.styles?.fontSize ?? "14px"}
            fontFamily={text.styles?.fontFamily ?? "sans-serif"}
            fontWeight={text.styles?.fontWeight ?? "normal"}
            stroke={isSelected ? "#B8860B" : "none"}
            strokeWidth={isSelected ? 0.5 : 0}
            style={{
              cursor: onTextClick ? "pointer" : "default",
              userSelect: "none",
            }}
            onClick={() => onTextClick?.(index)}
            onMouseEnter={() => onTextMouseEnter?.(index)}
            onMouseLeave={() => onTextMouseLeave?.()}
          >
            {text.content}
          </text>
        );
      })}
    </g>
  );
};
