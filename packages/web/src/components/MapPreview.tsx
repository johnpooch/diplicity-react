import { useEffect, useMemo, useRef, useState } from "react";
import type {
  GameListCurrentPhase,
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState } from "./InteractiveMap/toRenderState";
import { Skeleton } from "@/components/ui/skeleton";

type VariantForPreview = Pick<Variant, "nations" | "svgUrl">;

type MapPreviewProps = {
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase | GameListCurrentPhase;
  cover?: boolean;
  style?: React.CSSProperties;
  className?: string;
};

const MapPreview: React.FC<MapPreviewProps> = ({
  variant,
  phase,
  cover = false,
  style,
  className,
}) => {
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

export { MapPreview };
