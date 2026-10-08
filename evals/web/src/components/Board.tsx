import { useEffect, useMemo, useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import type { BoardState, OrderDetail } from "@/api";
import { DiplicityMap } from "@/board/mapRenderer";
import { toRenderState } from "@/board/toRenderState";
import CLASSICAL_DSVG from "@/board/classical.d.svg?raw";
import { Button } from "@/components/ui/button";
import { IDENTITY, panBy, wheelFactor, zoomAt, type View } from "@/zoom";

interface BoardProps {
  board: BoardState;
  orders: OrderDetail[];
}

const map = new DiplicityMap(CLASSICAL_DSVG);

const sizeOf = (element: HTMLElement) => ({
  width: element.clientWidth,
  height: element.clientHeight,
});

export const Board: React.FC<BoardProps> = ({ board, orders }) => {
  const svg = useMemo(() => map.render(toRenderState(board, orders)), [board, orders]);
  const container = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number } | null>(null);
  const [view, setView] = useState<View>(IDENTITY);

  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const rect = element.getBoundingClientRect();
      const factor = wheelFactor(event.deltaMode === 1 ? event.deltaY * 16 : event.deltaY);
      setView(current =>
        zoomAt(current, sizeOf(element), event.clientX - rect.left, event.clientY - rect.top, factor)
      );
    };
    element.addEventListener("wheel", onWheel, { passive: false });
    return () => element.removeEventListener("wheel", onWheel);
  }, []);

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = { x: event.clientX, y: event.clientY };
  };

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const start = drag.current;
    const element = container.current;
    if (!start || !element) return;
    drag.current = { x: event.clientX, y: event.clientY };
    setView(current =>
      panBy(current, sizeOf(element), event.clientX - start.x, event.clientY - start.y)
    );
  };

  const onPointerUp = () => {
    drag.current = null;
  };

  const zoomed = view.scale > 1;

  return (
    <div
      ref={container}
      className={`relative h-full touch-none overflow-hidden select-none ${zoomed ? "cursor-grab active:cursor-grabbing" : ""}`}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onDoubleClick={() => setView(IDENTITY)}
    >
      <div
        className="h-full origin-top-left [&>svg]:h-full [&>svg]:w-full"
        style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})` }}
        dangerouslySetInnerHTML={{ __html: svg }}
      />
      {zoomed && (
        <Button
          variant="outline"
          size="icon-sm"
          className="absolute top-2 right-2"
          aria-label="Reset zoom"
          onPointerDown={event => event.stopPropagation()}
          onClick={() => setView(IDENTITY)}
        >
          <RotateCcw />
        </Button>
      )}
    </div>
  );
};
