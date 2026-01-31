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

const FALLBACK_COLORS = {
  unit: { fill: "#4A90D9", innerDot: "#2563EB" },
  dislodged: { fill: "#EF4444", xMark: "#FFFFFF" },
  supplyCenter: { fill: "#F59E0B" },
} as const;

const DEFAULT_GRAY_COLORS = ["#666666", "#888888"];

function isUsingFallbackColor(color: string): boolean {
  return DEFAULT_GRAY_COLORS.includes(color.toLowerCase());
}

function darkenColor(hex: string, factor: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);

  const darkerR = Math.round(r * (1 - factor));
  const darkerG = Math.round(g * (1 - factor));
  const darkerB = Math.round(b * (1 - factor));

  return `#${darkerR.toString(16).padStart(2, "0")}${darkerG.toString(16).padStart(2, "0")}${darkerB.toString(16).padStart(2, "0")}`;
}

function getMarkerRadius(markerType: MarkerType): number {
  switch (markerType) {
    case "unit":
      return 14;
    case "dislodged":
      return 12;
    case "supplyCenter":
      return 12;
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
  const markerRef = useRef<SVGGElement>(null);
  const polygonRef = useRef<SVGPolygonElement>(null);

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (!svgRef.current) return;

      setIsDragging(true);
      const ref = markerType === "supplyCenter" ? polygonRef : markerRef;
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

      const ref = markerType === "supplyCenter" ? polygonRef : markerRef;
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

  const useFallback = isUsingFallbackColor(color);

  if (markerType === "supplyCenter") {
    const fillColor = useFallback ? FALLBACK_COLORS.supplyCenter.fill : color;
    const starPoints = generateStarPoints(displayX, displayY, radius, radius / 2, 5);
    return (
      <polygon
        ref={polygonRef}
        points={starPoints}
        fill={fillColor}
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

  if (markerType === "dislodged") {
    const fillColor = useFallback ? FALLBACK_COLORS.dislodged.fill : color;
    const xMarkColor = useFallback
      ? FALLBACK_COLORS.dislodged.xMark
      : darkenColor(color, 0.4);
    const xSize = radius * 0.5;

    return (
      <g
        ref={markerRef}
        style={{
          cursor: isDragging ? "grabbing" : "grab",
          touchAction: "none",
        }}
        onClick={handleClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <circle
          cx={displayX}
          cy={displayY}
          r={radius}
          fill={fillColor}
          stroke={selected ? "#FFD700" : "#333"}
          strokeWidth={selected ? 2 : 1}
        />
        <line
          x1={displayX - xSize}
          y1={displayY - xSize}
          x2={displayX + xSize}
          y2={displayY + xSize}
          stroke={xMarkColor}
          strokeWidth={2}
          strokeLinecap="round"
        />
        <line
          x1={displayX + xSize}
          y1={displayY - xSize}
          x2={displayX - xSize}
          y2={displayY + xSize}
          stroke={xMarkColor}
          strokeWidth={2}
          strokeLinecap="round"
        />
      </g>
    );
  }

  const fillColor = useFallback ? FALLBACK_COLORS.unit.fill : color;
  const innerDotColor = useFallback
    ? FALLBACK_COLORS.unit.innerDot
    : darkenColor(color, 0.3);

  return (
    <g
      ref={markerRef}
      style={{
        cursor: isDragging ? "grabbing" : "grab",
        touchAction: "none",
      }}
      onClick={handleClick}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <circle
        cx={displayX}
        cy={displayY}
        r={radius}
        fill={fillColor}
        stroke={selected ? "#FFD700" : "#333"}
        strokeWidth={selected ? 2 : 1}
      />
      <circle cx={displayX} cy={displayY} r={radius * 0.35} fill={innerDotColor} />
    </g>
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
