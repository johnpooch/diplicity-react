import { useMemo, useState } from "react";
import { Expand, Minus, Plus, RotateCcw } from "lucide-react";
import {
  TransformWrapper,
  TransformComponent,
} from "react-zoom-pan-pinch";

import type {
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState } from "./InteractiveMap/toRenderState";
import { MapPreview } from "./MapPreview";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";

type VariantForPreview = Pick<Variant, "nations" | "svgUrl">;

type ExpandableMapPreviewProps = {
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase;
  variantName?: string;
  style?: React.CSSProperties;
  className?: string;
};

const ZoomableMap: React.FC<{
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase;
}> = ({ variant, phase }) => {
  const { data: dsvg } = useDsvg(variant.svgUrl, true);

  const svg = useMemo(() => {
    if (!dsvg) return null;
    const renderState = toRenderState(variant, phase, [], [], []);
    return new DiplicityMap(dsvg)
      .render(renderState)
      .replace(
        "<svg ",
        '<svg preserveAspectRatio="xMidYMid meet" width="100%" height="100%" '
      );
  }, [dsvg, variant, phase]);

  if (!svg) {
    return <Skeleton className="w-full h-full" />;
  }

  return (
    <TransformWrapper
      minScale={1}
      maxScale={8}
      centerOnInit
      doubleClick={{ mode: "zoomIn", step: 0.7 }}
    >
      {({ zoomIn, zoomOut, resetTransform }) => (
        <>
          <TransformComponent
            wrapperStyle={{ width: "100%", height: "100%" }}
            contentStyle={{ width: "100%", height: "100%" }}
          >
            <div
              className="w-full h-full"
              dangerouslySetInnerHTML={{ __html: svg }}
            />
          </TransformComponent>
          <div className="absolute bottom-4 right-4 flex flex-col gap-2">
            <Button
              size="icon"
              variant="secondary"
              className="rounded-full shadow-lg"
              onClick={() => zoomIn()}
              aria-label="Zoom in"
            >
              <Plus />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              className="rounded-full shadow-lg"
              onClick={() => zoomOut()}
              aria-label="Zoom out"
            >
              <Minus />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              className="rounded-full shadow-lg"
              onClick={() => resetTransform()}
              aria-label="Reset zoom"
            >
              <RotateCcw />
            </Button>
          </div>
        </>
      )}
    </TransformWrapper>
  );
};

const ExpandableMapPreview: React.FC<ExpandableMapPreviewProps> = ({
  variant,
  phase,
  variantName,
  style,
  className,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`group relative block w-full cursor-zoom-in ${className ?? ""}`}
        style={style}
        aria-label="Expand map preview"
      >
        <MapPreview
          variant={variant}
          phase={phase}
          style={{ width: "100%", height: "100%" }}
        />
        <span className="absolute bottom-2 right-2 flex size-8 items-center justify-center rounded-full bg-background/80 text-foreground shadow-sm transition-opacity group-hover:bg-background">
          <Expand className="size-4" />
        </span>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          aria-describedby={undefined}
          className="h-[90vh] w-[95vw] max-w-5xl gap-0 overflow-hidden p-0"
        >
          <DialogTitle className="sr-only">
            {variantName ? `${variantName} map` : "Map preview"}
          </DialogTitle>
          <div className="relative h-full w-full">
            <ZoomableMap variant={variant} phase={phase} />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export { ExpandableMapPreview };
