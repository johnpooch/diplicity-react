import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  TransformWrapper,
  TransformComponent,
  type ReactZoomPanPinchContentRef,
} from "react-zoom-pan-pinch";
import type { Variant } from "@/api/generated/endpoints";
import { MapVisual } from "@/components/InteractiveMap/MapVisual";
import { MapHitLayer } from "@/components/InteractiveMap/MapHitLayer";
import { parseDsvg } from "@/components/InteractiveMap/dsvgParser";
import { DiplicityMap } from "@/components/InteractiveMap/mapRenderer";
import { toRenderState } from "@/components/InteractiveMap/toRenderState";
import {
  applyViewBox,
  transformToViewBox,
  type Dimensions,
  type TransformState,
} from "@/components/InteractiveMap/viewBoxZoom";
import { isNativePlatform } from "@/utils/platform";
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

  const mapVisualRef = useRef<SVGSVGElement>(null);
  const hitRef = useRef<SVGSVGElement>(null);
  const transformRef = useRef<ReactZoomPanPinchContentRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const containerSizeRef = useRef<Dimensions | null>(null);
  const [container, setContainer] = useState<Dimensions | null>(null);
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  const isNative = isNativePlatform();
  const mapViewBox = parsedDsvg?.viewBox;

  const renderState = useMemo(
    () => toRenderState(variant, board.phase, board.orders ?? [], selected, highlighted),
    [variant, board.phase, board.orders, selected, highlighted]
  );

  const syncViewBox = (state: TransformState) => {
    const size = containerSizeRef.current;
    if (!size || !mapViewBox) return;
    applyViewBox(
      mapVisualRef.current,
      transformToViewBox(state, size, mapViewBox)
    );
  };

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        containerSizeRef.current = { width, height };
        setContainer({ width, height });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Seed the visible layer's viewBox before first paint; the transform sync
  // refines it once react-zoom-pan-pinch centres on init.
  useLayoutEffect(() => {
    if (mapViewBox) {
      applyViewBox(mapVisualRef.current, mapViewBox);
    }
  }, [mapViewBox]);

  const focusKey = focus.join(",");
  useEffect(() => {
    const hit = hitRef.current;
    if (!hit || !container || !parsedDsvg || focus.length === 0) return;

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
        const el = hit.querySelector<SVGGraphicsElement>(
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
        container.width / (boxWidth * FOCUS_PADDING),
        container.height / (boxHeight * FOCUS_PADDING)
      );
      const centerPxX = minX + boxWidth / 2 - viewBox.minX;
      const centerPxY = minY + boxHeight / 2 - viewBox.minY;
      const posX = container.width / 2 - centerPxX * scale;
      const posY = container.height / 2 - centerPxY * scale;
      transform.setTransform(posX, posY, scale, FOCUS_ANIMATION_MS);
    });
    return () => cancelAnimationFrame(raf);
  }, [focusKey, container, parsedDsvg, focus]);

  const handleGesture = (disabled: boolean) => {
    if (hitRef.current) {
      hitRef.current.style.pointerEvents = disabled ? "none" : "";
    }
  };

  if (!parsedDsvg || !renderer) {
    return <div ref={containerRef} className="h-full w-full" />;
  }

  return (
    <div ref={containerRef} className="relative h-full w-full">
      <MapVisual
        svgRef={mapVisualRef}
        parsedDsvg={parsedDsvg}
        renderer={renderer}
        renderState={renderState}
        hoveredProvince={hoveredProvince}
        selected={selected}
      />
      <div style={{ position: "absolute", inset: 0 }}>
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
          onTransformed={(_ref, state) => syncViewBox(state)}
          onPanningStart={() => handleGesture(true)}
          onPanningStop={() => handleGesture(false)}
          onPinchingStart={() => handleGesture(true)}
          onPinchingStop={() => handleGesture(false)}
        >
          <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
            <MapHitLayer
              svgRef={hitRef}
              parsedDsvg={parsedDsvg}
              interactive
              isNative={isNative}
              renderableProvinces={tappable}
              onHover={setHoveredProvince}
              onClickProvince={province => onProvinceClick(province)}
            />
          </TransformComponent>
        </TransformWrapper>
      </div>
    </div>
  );
};

export { TutorialMap };
