import { useMemo, useState } from "react";
import { Expand, X } from "lucide-react";
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
  DialogClose,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";

type VariantForPreview = Pick<Variant, "name" | "nations" | "svgUrl">;

type ExpandableMapPreviewProps = {
  variant: VariantForPreview;
  phase: PhaseRetrieve | VariantTemplatePhase;
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
      <TransformComponent
        wrapperStyle={{ width: "100%", height: "100%" }}
        contentStyle={{ width: "100%", height: "100%" }}
      >
        <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: svg }} />
      </TransformComponent>
    </TransformWrapper>
  );
};

const ExpandableMapPreview: React.FC<ExpandableMapPreviewProps> = ({
  variant,
  phase,
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
          showCloseButton={false}
          aria-describedby={undefined}
          className="h-[100dvh] w-screen max-w-none gap-0 overflow-hidden rounded-none border-0 bg-black/95 p-0"
        >
          <DialogTitle className="sr-only">{`${variant.name} map`}</DialogTitle>
          <DialogClose asChild>
            <Button
              size="icon"
              aria-label="Close"
              className="absolute right-4 top-[calc(var(--safe-area-top)+1rem)] z-10 size-10 rounded-full bg-black/60 text-white hover:bg-black/80"
            >
              <X className="size-5" />
            </Button>
          </DialogClose>
          <div className="relative h-full w-full">
            <ZoomableMap variant={variant} phase={phase} />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export { ExpandableMapPreview };
