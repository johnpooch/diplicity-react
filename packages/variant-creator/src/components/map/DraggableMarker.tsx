import { useRef, useState, useCallback, useEffect } from "react";
import type { Position } from "@/types/variant";

export type MarkerType = "unit" | "dislodged" | "supplyCenter";

interface DraggableMarkerProps {
  x: number;
  y: number;
  color: string;
  selected: boolean;
  markerType: MarkerType;
  onClick: () => void;
  onDrag: (newPosition: Position) => void;
  svgRef: React.RefObject<SVGSVGElement | null>;
}

function getMarkerRadius(markerType: MarkerType): number {
  switch (markerType) {
    case "unit":
      return 12;
    case "dislodged":
      return 10;
    case "supplyCenter":
      return 8;
  }
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

export const DraggableMarker: React.FC<DraggableMarkerProps> = ({
  x,
  y,
  color,
  selected,
  markerType,
  onClick,
  onDrag,
  svgRef,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragPosition, setDragPosition] = useState<Position | null>(null);
  const circleRef = useRef<SVGCircleElement>(null);
  const polygonRef = useRef<SVGPolygonElement>(null);

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (!svgRef.current) return;

      setIsDragging(true);
      const ref = markerType === "supplyCenter" ? polygonRef : circleRef;
      ref.current?.setPointerCapture(e.pointerId);

      const svgCoords = screenToSvgCoords(svgRef.current, e.clientX, e.clientY);
      setDragPosition(svgCoords);
    },
    [svgRef, markerType]
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

      const ref = markerType === "supplyCenter" ? polygonRef : circleRef;
      ref.current?.releasePointerCapture(e.pointerId);
      setIsDragging(false);

      if (dragPosition) {
        onDrag(dragPosition);
      }
      setDragPosition(null);
    },
    [isDragging, dragPosition, onDrag, markerType]
  );

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) {
        e.stopPropagation();
        onClick();
      }
    },
    [isDragging, onClick]
  );

  useEffect(() => {
    const handleGlobalPointerUp = () => {
      if (isDragging) {
        setIsDragging(false);
        if (dragPosition) {
          onDrag(dragPosition);
        }
        setDragPosition(null);
      }
    };

    if (isDragging) {
      window.addEventListener("pointerup", handleGlobalPointerUp);
    }

    return () => {
      window.removeEventListener("pointerup", handleGlobalPointerUp);
    };
  }, [isDragging, dragPosition, onDrag]);

  const radius = getMarkerRadius(markerType);
  const displayX = dragPosition?.x ?? x;
  const displayY = dragPosition?.y ?? y;

  if (markerType === "supplyCenter") {
    const starPoints = generateStarPoints(displayX, displayY, radius, radius / 2, 5);
    return (
      <polygon
        ref={polygonRef}
        points={starPoints}
        fill={color}
        stroke={selected ? "#FFD700" : "#333"}
        strokeWidth={selected ? 2 : 1}
        style={{
          cursor: isDragging ? "grabbing" : "grab",
          touchAction: "none",
        }}
        onClick={handleClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      />
    );
  }

  return (
    <circle
      ref={circleRef}
      cx={displayX}
      cy={displayY}
      r={radius}
      fill={color}
      stroke={selected ? "#FFD700" : "#333"}
      strokeWidth={selected ? 2 : 1}
      strokeDasharray={markerType === "dislodged" ? "3,2" : undefined}
      style={{
        cursor: isDragging ? "grabbing" : "grab",
        touchAction: "none",
      }}
      onClick={handleClick}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    />
  );
};

function generateStarPoints(
  cx: number,
  cy: number,
  outerRadius: number,
  innerRadius: number,
  points: number
): string {
  const angle = Math.PI / points;
  const result: string[] = [];

  for (let i = 0; i < points * 2; i++) {
    const radius = i % 2 === 0 ? outerRadius : innerRadius;
    const currentAngle = i * angle - Math.PI / 2;
    const x = cx + Math.cos(currentAngle) * radius;
    const y = cy + Math.sin(currentAngle) * radius;
    result.push(`${x},${y}`);
  }

  return result.join(" ");
}
