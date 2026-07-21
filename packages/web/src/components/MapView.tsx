import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { ComponentType } from "react";
import type {
  GameListCurrentPhase,
  Order,
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState } from "./InteractiveMap/toRenderState";
import { Skeleton } from "@/components/ui/skeleton";
import type { GameMapCanvasProps } from "./GameMapCanvas/GameMapCanvas";
import type { MapMode } from "./GameMapCanvas/GameMapController";
import { healLazyImport, StaleChunkFallback } from "../utils/lazyScreen";

const GameMapCanvas = lazy(() =>
  healLazyImport<ComponentType<GameMapCanvasProps>>(
    async () => (await import("./GameMapCanvas/GameMapCanvas"))?.GameMapCanvas,
    StaleChunkFallback
  )
);

type MapPhase = PhaseRetrieve | VariantTemplatePhase | GameListCurrentPhase;

interface MapViewProps {
  variant: Pick<Variant, "id" | "nations" | "svgUrl">;
  phase: MapPhase;
  orders?: Order[];
  selected?: string[];
  highlighted?: string[];
  civilDisorderNations?: string[];
  renderableProvinces?: string[];
  mode?: MapMode;
  cover?: boolean;
  showFillToggle?: boolean;
  focus?: string[];
  onClickProvince?: (province: string, position: { x: number; y: number }) => void;
  style?: React.CSSProperties;
  className?: string;
}

// Static render path: the composed board SVG, lazily rendered once it scrolls
// into view. No Leaflet — this keeps the many thumbnails on list screens light.
const StaticMap: React.FC<{
  variant: Pick<Variant, "nations" | "svgUrl">;
  phase: MapPhase;
  cover?: boolean;
  style?: React.CSSProperties;
  className?: string;
}> = ({ variant, phase, cover = false, style, className }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    let root: HTMLElement | null = el.parentElement;
    while (root) {
      const overflow = window.getComputedStyle(root).overflowY;
      if (overflow === "auto" || overflow === "scroll") break;
      root = root.parentElement;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { root, rootMargin: "200px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const { data: dsvg } = useDsvg(variant.svgUrl, inView);

  const svg = useMemo(() => {
    if (!dsvg) return null;
    const renderState = toRenderState(variant, phase, [], [], []);
    const rendered = new DiplicityMap(dsvg).render(renderState);
    if (cover) {
      return rendered.replace(
        "<svg ",
        '<svg preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
      );
    }
    return rendered;
  }, [dsvg, variant, phase, cover]);

  return (
    <div ref={containerRef} className={className} style={style}>
      {svg ? (
        <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: svg }} />
      ) : (
        <Skeleton className="w-full h-full" />
      )}
    </div>
  );
};

const MapView: React.FC<MapViewProps> = ({ mode = "interactive", ...props }) => {
  if (mode === "static") {
    return (
      <StaticMap
        variant={props.variant}
        phase={props.phase}
        cover={props.cover}
        style={props.style}
        className={props.className}
      />
    );
  }

  return (
    <Suspense fallback={<div style={{ width: "100%", height: "100%" }} />}>
      <GameMapCanvas
        variant={props.variant}
        phase={props.phase}
        orders={props.orders}
        selected={props.selected ?? []}
        highlighted={props.highlighted}
        civilDisorderNations={props.civilDisorderNations}
        renderableProvinces={props.renderableProvinces}
        mode={mode}
        showFillToggle={props.showFillToggle}
        focus={props.focus}
        onClickProvince={props.onClickProvince}
        style={props.style}
      />
    </Suspense>
  );
};

export { MapView };
export type { MapViewProps };
