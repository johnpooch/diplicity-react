import { useMemo } from "react";
import type {
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { useCustomNationColours } from "../hooks/useCustomNationColours";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState } from "./InteractiveMap/toRenderState";
import { Skeleton } from "@/components/ui/skeleton";

type VariantForPreview = Pick<Variant, "nations" | "svgUrl">;

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
  const applyCustomColours = useCustomNationColours();

  const variantWithColours = useMemo(
    () => ({ ...variant, nations: applyCustomColours(variant.nations) }),
    [variant, applyCustomColours],
  );

  const svg = useMemo(() => {
    if (!dsvg) return null;
    const renderState = toRenderState(variantWithColours, phase, [], [], []);
    return new DiplicityMap(dsvg).render(renderState);
  }, [dsvg, variantWithColours, phase]);

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
