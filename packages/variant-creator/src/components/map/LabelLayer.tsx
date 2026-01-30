import { useState, useRef, useCallback } from "react";
import type { Province, Position } from "@/types/variant";
import type { SelectedElement } from "./MarkerLayer";

interface LabelLayerProps {
  provinces: Province[];
  selectedElement: SelectedElement | null;
  onLabelClick: (provinceId: string, labelIndex: number) => void;
  onLabelDrag: (
    provinceId: string,
    labelIndex: number,
    position: Position
  ) => void;
  onLabelDoubleClick: (provinceId: string, labelIndex: number) => void;
  visible: boolean;
  svgRef: React.RefObject<SVGSVGElement | null>;
}

function screenToSvgCoords(
  svgElement: SVGSVGElement,
  screenX: number,
  screenY: number
): Position {
  const point = svgElement.createSVGPoint();
  point.x = screenX;
  point.y = screenY;
  const ctm = svgElement.getScreenCTM();
  if (!ctm) {
    return { x: screenX, y: screenY };
  }
  const svgPoint = point.matrixTransform(ctm.inverse());
  return { x: svgPoint.x, y: svgPoint.y };
}

interface DraggableLabelProps {
  provinceId: string;
  labelIndex: number;
  text: string;
  x: number;
  y: number;
  rotation?: number;
  fontSize?: string;
  fontFamily?: string;
  fontWeight?: string;
  fill?: string;
  selected: boolean;
  onLabelClick: (provinceId: string, labelIndex: number) => void;
  onLabelDrag: (
    provinceId: string,
    labelIndex: number,
    position: Position
  ) => void;
  onLabelDoubleClick: (provinceId: string, labelIndex: number) => void;
  svgRef: React.RefObject<SVGSVGElement | null>;
}

const DraggableLabel: React.FC<DraggableLabelProps> = ({
  provinceId,
  labelIndex,
  text,
  x,
  y,
  rotation,
  fontSize,
  fontFamily,
  fontWeight,
  fill,
  selected,
  onLabelClick,
  onLabelDrag,
  onLabelDoubleClick,
  svgRef,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragPosition, setDragPosition] = useState<Position | null>(null);
  const textRef = useRef<SVGTextElement>(null);

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (!svgRef.current) return;

      setIsDragging(true);
      textRef.current?.setPointerCapture(e.pointerId);

      const svgCoords = screenToSvgCoords(svgRef.current, e.clientX, e.clientY);
      setDragPosition(svgCoords);
    },
    [svgRef]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isDragging || !svgRef.current) return;

      e.preventDefault();
      e.stopPropagation();

      const svgCoords = screenToSvgCoords(svgRef.current, e.clientX, e.clientY);
      setDragPosition(svgCoords);
    },
    [isDragging, svgRef]
  );

  const handlePointerUp = useCallback(
    (e: React.PointerEvent) => {
      if (!isDragging) return;

      e.preventDefault();
      e.stopPropagation();

      textRef.current?.releasePointerCapture(e.pointerId);
      setIsDragging(false);

      if (dragPosition) {
        onLabelDrag(provinceId, labelIndex, dragPosition);
      }
      setDragPosition(null);
    },
    [isDragging, dragPosition, onLabelDrag, provinceId, labelIndex]
  );

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) {
        e.stopPropagation();
        onLabelClick(provinceId, labelIndex);
      }
    },
    [isDragging, onLabelClick, provinceId, labelIndex]
  );

  const handleDoubleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onLabelDoubleClick(provinceId, labelIndex);
    },
    [onLabelDoubleClick, provinceId, labelIndex]
  );

  const displayX = dragPosition?.x ?? x;
  const displayY = dragPosition?.y ?? y;

  const transform = rotation
    ? `rotate(${rotation}, ${displayX}, ${displayY})`
    : undefined;

  return (
    <text
      ref={textRef}
      x={displayX}
      y={displayY}
      transform={transform}
      fill={selected ? "#FFD700" : fill ?? "#333333"}
      fontSize={fontSize ?? "14px"}
      fontFamily={fontFamily ?? "sans-serif"}
      fontWeight={fontWeight ?? "normal"}
      stroke={selected ? "#B8860B" : "none"}
      strokeWidth={selected ? 0.5 : 0}
      style={{
        cursor: isDragging ? "grabbing" : "grab",
        userSelect: "none",
        touchAction: "none",
      }}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      {text}
    </text>
  );
};

export const LabelLayer: React.FC<LabelLayerProps> = ({
  provinces,
  selectedElement,
  onLabelClick,
  onLabelDrag,
  onLabelDoubleClick,
  visible,
  svgRef,
}) => {
  if (!visible) {
    return null;
  }

  return (
    <g className="label-layer">
      {provinces.map((province) =>
        province.labels.map((label, labelIndex) => {
          const isSelected =
            selectedElement?.type === "label" &&
            selectedElement?.provinceId === province.id &&
            selectedElement?.labelIndex === labelIndex;

          return (
            <DraggableLabel
              key={`${province.id}-label-${labelIndex}`}
              provinceId={province.id}
              labelIndex={labelIndex}
              text={label.text}
              x={label.position.x}
              y={label.position.y}
              rotation={label.rotation}
              fontSize={label.styles?.fontSize}
              fontFamily={label.styles?.fontFamily}
              fontWeight={label.styles?.fontWeight}
              fill={label.styles?.fill}
              selected={isSelected}
              onLabelClick={onLabelClick}
              onLabelDrag={onLabelDrag}
              onLabelDoubleClick={onLabelDoubleClick}
              svgRef={svgRef}
            />
          );
        })
      )}
    </g>
  );
};
