import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Expand, X } from "lucide-react";
import {
  TransformWrapper,
  TransformComponent,
  type ReactZoomPanPinchContentRef,
} from "react-zoom-pan-pinch";

import type {
  PhaseRetrieve,
  Variant,
  VariantTemplatePhase,
} from "../api/generated/endpoints";
import { useDsvg } from "../hooks/useDsvg";
import { parseDsvg } from "./InteractiveMap/dsvgParser";
import { DiplicityMap } from "./InteractiveMap/mapRenderer";
import { toRenderState } from "./InteractiveMap/toRenderState";
import { MapVisual } from "./InteractiveMap/MapVisual";
import { MapHitLayer } from "./InteractiveMap/MapHitLayer";
import {
  applyViewBox,
  transformToViewBox,
  type Dimensions,
  type TransformState,
} from "./InteractiveMap/viewBoxZoom";
import { MapPreview } from "./MapPreview";
import { Button } from "@/components/ui/button";
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
  const containerRef = useRef<HTMLDivElement>(null);
  const mapVisualRef = useRef<SVGSVGElement>(null);
  const hitRef = useRef<SVGSVGElement>(null);
  const transformRef = useRef<ReactZoomPanPinchContentRef>(null);
  const containerSizeRef = useRef<Dimensions | null>(null);

  const { data: dsvg } = useDsvg(variant.svgUrl, true);
  const parsedDsvg = useMemo(() => (dsvg ? parseDsvg(dsvg) : null), [dsvg]);
  const renderer = useMemo(() => (dsvg ? new DiplicityMap(dsvg) : null), [dsvg]);
  const renderState = useMemo(
    () => toRenderState(variant, phase, [], [], []),
    [variant, phase]
  );

  const [container, setContainer] = useState<Dimensions>();

  const mapViewBox = parsedDsvg?.viewBox;
  const containedScale =
    container && mapViewBox
      ? Math.min(
          container.width / mapViewBox.width,
          container.height / mapViewBox.height
        )
      : 1;

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

  useLayoutEffect(() => {
    if (mapViewBox) {
      applyViewBox(mapVisualRef.current, mapViewBox);
    }
  }, [mapViewBox]);

  useEffect(() => {
    if (transformRef.current && container && mapViewBox) {
      const scaledWidth = mapViewBox.width * containedScale;
      const scaledHeight = mapViewBox.height * containedScale;
      const centerX = (container.width - scaledWidth) / 2;
      const centerY = (container.height - scaledHeight) / 2;
      transformRef.current.setTransform(centerX, centerY, containedScale, 0);
    }
  }, [containedScale, container, mapViewBox]);

  return (
    <div ref={containerRef} className="relative h-full w-full">
      {parsedDsvg && renderer ? (
        <>
          <MapVisual
            svgRef={mapVisualRef}
            parsedDsvg={parsedDsvg}
            renderer={renderer}
            renderState={renderState}
            hoveredProvince={null}
            selected={[]}
          />
          <div style={{ position: "absolute", inset: 0 }}>
            <TransformWrapper
              ref={transformRef}
              minScale={containedScale}
              maxScale={containedScale * 8}
              centerOnInit
              limitToBounds
              centerZoomedOut
              disablePadding
              doubleClick={{ mode: "zoomIn", step: 0.7 }}
              panning={{ velocityDisabled: true }}
              velocityAnimation={{ disabled: true }}
              onTransformed={(_ref, state) => syncViewBox(state)}
            >
              <TransformComponent
                wrapperStyle={{ width: "100%", height: "100%" }}
              >
                <MapHitLayer
                  svgRef={hitRef}
                  parsedDsvg={parsedDsvg}
                  isNative={false}
                  onHover={() => {}}
                />
              </TransformComponent>
            </TransformWrapper>
          </div>
        </>
      ) : null}
    </div>
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
