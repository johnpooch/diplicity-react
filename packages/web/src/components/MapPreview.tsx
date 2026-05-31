import { useEffect, useMemo, useRef, useState } from "react";
import type {
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState, type PhaseForPreview } from "./InteractiveMap/toRenderState";
import { Skeleton } from "@/components/ui/skeleton";
import type { Point } from "./InteractiveMap/dsvgParser";

// Parse each variant's DSVG once per session regardless of how many game cards use it.
const diplicityMapCache = new Map<string, DiplicityMap>();

const getCachedMap = (svgUrl: string, dsvg: string): DiplicityMap => {
  let map = diplicityMapCache.get(svgUrl);
  if (!map) {
    map = new DiplicityMap(dsvg);
    diplicityMapCache.set(svgUrl, map);
  }
  return map;
};

type VariantForPreview = Pick<Variant, "nations" | "svgUrl">;

type VariantForGameCardMap = Pick<Variant, "nations" | "svgUrl" | "templatePhase">;

const makeGameCardMap =
  (variant: VariantForGameCardMap) =>
  (focusProvinceIds?: string[]) => (
    <MapPreview
      variant={variant}
      phase={variant.templatePhase}
      focusProvinceIds={focusProvinceIds}
      thumbnail
      className="w-full h-full"
    />
  );

type MapPreviewProps = {
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase | PhaseForPreview;
  /** Province IDs to center the thumbnail on (player's home supply centers). */
  focusProvinceIds?: string[];
  /** Render a lightweight thumbnail (skips province names + foreground layers). */
  thumbnail?: boolean;
  style?: React.CSSProperties;
  className?: string;
};

const computeFocusViewBox = (
  centers: Point[],
  fullWidth: number,
  fullHeight: number,
  fullMinX: number,
  fullMinY: number
): string => {
  const minX = Math.min(...centers.map(p => p.x));
  const maxX = Math.max(...centers.map(p => p.x));
  const minY = Math.min(...centers.map(p => p.y));
  const maxY = Math.max(...centers.map(p => p.y));

  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;

  // Size the view to show the nation's spread plus generous context.
  // Minimum of 30% of the shorter map dimension so it never gets too tight.
  const spread = Math.max(maxX - minX, maxY - minY);
  const viewSize = Math.max(spread + 300, Math.min(fullWidth, fullHeight) * 0.3);

  // Square viewBox — preserveAspectRatio="slice" fills the container.
  // Clamp so the viewBox never extends beyond either edge of the map.
  const left = Math.max(fullMinX, Math.min(fullMinX + fullWidth - viewSize, cx - viewSize / 2));
  const top = Math.max(fullMinY, Math.min(fullMinY + fullHeight - viewSize, cy - viewSize / 2));

  return `${left} ${top} ${viewSize} ${viewSize}`;
};

const MapPreview: React.FC<MapPreviewProps> = ({
  variant,
  phase,
  focusProvinceIds,
  thumbnail = false,
  style,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [shouldLoad, setShouldLoad] = useState(false);

  useEffect(() => {
    if (!("IntersectionObserver" in window)) {
      setShouldLoad(true);
      return;
    }
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShouldLoad(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const { data: dsvg } = useDsvg(shouldLoad ? variant.svgUrl : null);

  const svg = useMemo(() => {
    if (!dsvg || !variant.svgUrl) return null;
    const renderState = toRenderState(variant, phase as PhaseForPreview, [], [], []);
    const map = getCachedMap(variant.svgUrl, dsvg);
    let raw = thumbnail ? map.renderThumbnail(renderState) : map.render(renderState);

    // Always fill the container (slice rather than meet); clip content to viewBox.
    raw = raw.replace(
      "<svg ",
      '<svg width="100%" height="100%" overflow="hidden" preserveAspectRatio="xMidYMid slice" '
    );

    // If focus provinces provided, zoom the viewBox in on them.
    if (focusProvinceIds && focusProvinceIds.length > 0) {
      const centers = focusProvinceIds
        .map(id => map.getProvinceCenter(id))
        .filter((p): p is Point => p !== undefined);

      if (centers.length > 0) {
        const vb = map.getViewBox();
        const focusAttr = computeFocusViewBox(
          centers,
          vb.width,
          vb.height,
          vb.minX,
          vb.minY
        );
        raw = raw.replace(/viewBox="[^"]*"/, `viewBox="${focusAttr}"`);
      }
    }

    return raw;
  }, [dsvg, variant, phase, focusProvinceIds, thumbnail]);

  if (!svg) {
    return (
      <div ref={containerRef} className={className} style={style}>
        <Skeleton className="w-full h-full" />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={className}
      style={style}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};

export { MapPreview, makeGameCardMap };
