import { useMemo } from "react";
import type {
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState } from "./InteractiveMap/toRenderState";
import { Skeleton } from "@/components/ui/skeleton";

type VariantForPreview = Pick<Variant, "nations" | "provinces" | "dominanceRules" | "svgUrl">;

type MapPreviewProps = {
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase;
  style?: React.CSSProperties;
  className?: string;
};

const MapPreview: React.FC<MapPreviewProps> = ({
  variant,
  phase,
  style,
  className,
}) => {
  const { data: dsvg } = useDsvg(variant.svgUrl);

  const svg = useMemo(() => {
    if (!dsvg) return null;
    const renderState = toRenderState(variant, phase, [], [], []);
    return new DiplicityMap(dsvg).render(renderState);
  }, [dsvg, variant, phase]);

  if (!svg) {
    return <Skeleton className={className} style={style} />;
  }

  return (
    <div
      className={className}
      style={style}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};

export { MapPreview };
