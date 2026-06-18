import { useEffect, useMemo, useRef, useState } from "react";
import {
  TransformWrapper,
  TransformComponent,
  type ReactZoomPanPinchContentRef,
} from "react-zoom-pan-pinch";
import type { Variant } from "@/api/generated/endpoints";
import { InteractiveMap } from "@/components/InteractiveMap/InteractiveMap";
import { parseDsvg } from "@/components/InteractiveMap/dsvgParser";
import { DiplicityMap } from "@/components/InteractiveMap/mapRenderer";
import { useDsvg } from "@/hooks/useDsvg";
import type { Board } from "../types";

interface TutorialMapProps {
  variant: Variant;
  board: Board;
  selected: string[];
  highlighted: string[];
  tappable: string[];
  focus: string[];
  onProvinceClick: (province: string) => void;
}

const FOCUS_PADDING = 1.4;
const FOCUS_ANIMATION_MS = 400;

const TutorialMap: React.FC<TutorialMapProps> = ({
  variant,
  board,
  selected,
  highlighted,
  tappable,
  focus,
  onProvinceClick,
}) => {
  const { data: dsvg } = useDsvg(variant.svgUrl);
  const parsedDsvg = useMemo(() => (dsvg ? parseDsvg(dsvg) : null), [dsvg]);
  const renderer = useMemo(() => (dsvg ? new DiplicityMap(dsvg) : null), [dsvg]);

  const svgRef = useRef<SVGSVGElement>(null);
  const transformRef = useRef<ReactZoomPanPinchContentRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [container, setContainer] = useState<{ w: number; h: number } | null>(
    null
  );

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setContainer({ w: width, h: height });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const focusKey = focus.join(",");
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || !container || !parsedDsvg || focus.length === 0) return;

    // Deferred so it runs after TransformWrapper's own initialisation, which
    // otherwise resets the transform we set here.
    const raf = requestAnimationFrame(() => {
      const transform = transformRef.current;
      if (!transform) return;

      let minX = Infinity;
      let minY = Infinity;
      let maxX = -Infinity;
      let maxY = -Infinity;
      for (const id of focus) {
        const el = svg.querySelector<SVGGraphicsElement>(
          `[id="${CSS.escape(id)}"]`
        );
        if (!el) continue;
        const box = el.getBBox();
        minX = Math.min(minX, box.x);
        minY = Math.min(minY, box.y);
        maxX = Math.max(maxX, box.x + box.width);
        maxY = Math.max(maxY, box.y + box.height);
      }
      if (!isFinite(minX)) return;

      const { viewBox } = parsedDsvg;
      const boxWidth = maxX - minX;
      const boxHeight = maxY - minY;
      const scale = Math.min(
        container.w / (boxWidth * FOCUS_PADDING),
        container.h / (boxHeight * FOCUS_PADDING)
      );
      const centerPxX = minX + boxWidth / 2 - viewBox.minX;
      const centerPxY = minY + boxHeight / 2 - viewBox.minY;
      const posX = container.w / 2 - centerPxX * scale;
      const posY = container.h / 2 - centerPxY * scale;
      transform.setTransform(posX, posY, scale, FOCUS_ANIMATION_MS);
    });
    return () => cancelAnimationFrame(raf);
  }, [focusKey, container, parsedDsvg, focus]);

  const handleGesture = (disabled: boolean) => {
    if (svgRef.current) {
      svgRef.current.style.pointerEvents = disabled ? "none" : "";
    }
  };

  if (!parsedDsvg || !renderer) {
    return <div ref={containerRef} className="h-full w-full" />;
  }

  return (
    <div ref={containerRef} className="h-full w-full">
      <TransformWrapper
        ref={transformRef}
        minScale={0.2}
        maxScale={8}
        limitToBounds={true}
        centerOnInit={true}
        disablePadding
        doubleClick={{ disabled: true }}
        panning={{ velocityDisabled: true }}
        velocityAnimation={{ disabled: true }}
        onPanningStart={() => handleGesture(true)}
        onPanningStop={() => handleGesture(false)}
        onPinchingStart={() => handleGesture(true)}
        onPinchingStop={() => handleGesture(false)}
      >
        <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
          <InteractiveMap
            ref={svgRef}
            interactive
            variant={variant}
            phase={board.phase}
            orders={board.orders}
            selected={selected}
            highlighted={highlighted}
            renderableProvinces={tappable}
            parsedDsvg={parsedDsvg}
            renderer={renderer}
            onClickProvince={province => onProvinceClick(province)}
          />
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
};

export { TutorialMap };
