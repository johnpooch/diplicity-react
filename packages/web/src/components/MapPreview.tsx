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

type VariantForPreview = Pick<Variant, "nations" | "svgUrl">;

type MapPreviewProps = {
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase;
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
  const { data: dsvg } = useDsvg(variant.svgUrl);

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
