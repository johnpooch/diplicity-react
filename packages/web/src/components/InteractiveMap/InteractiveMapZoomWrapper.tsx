import {
  TransformWrapper,
  TransformComponent,
  ReactZoomPanPinchContentRef,
} from "react-zoom-pan-pinch";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Maximize, Minimize } from "lucide-react";
import { Button } from "@/components/ui/button";

import { MapVisual } from "./MapVisual";
import { MapHitLayer } from "./MapHitLayer";
import { useDsvg } from "../../hooks/useDsvg";
import { parseDsvg } from "./dsvgParser";
import { DiplicityMap } from "./mapRenderer";
import { toRenderState } from "./toRenderState";
import {
  applyViewBox,
  transformToViewBox,
  type Dimensions,
  type TransformState,
} from "./viewBoxZoom";
import { isNativePlatform } from "../../utils/platform";
import type {
  Order,
  PhaseRetrieve,
  Variant,
} from "../../api/generated/endpoints";

type VariantForMap = Pick<Variant, "id" | "nations" | "svgUrl">;

type InteractiveMapContentProps = {
  interactive?: boolean;
  variant: VariantForMap;
  phase: PhaseRetrieve;
  selected: string[];
  highlighted?: string[];
  civilDisorderNations?: string[];
  orders: Order[] | undefined;
  renderableProvinces?: string[];
  onClickProvince?: (
    province: string,
    event: React.MouseEvent<SVGPathElement>
  ) => void;
};

type InteractiveMapZoomWrapperProps = {
  interactiveMapProps: InteractiveMapContentProps;
};

const InteractiveMapZoomWrapper: React.FC<InteractiveMapZoomWrapperProps> = ({
  interactiveMapProps,
}) => {
  const mapVisualRef = useRef<SVGSVGElement>(null);
  const hitRef = useRef<SVGSVGElement>(null);
  const transformRef = useRef<ReactZoomPanPinchContentRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const containerSizeRef = useRef<Dimensions | null>(null);

  const isNative = isNativePlatform();

  const { data: dsvg, isLoading } = useDsvg(interactiveMapProps.variant.svgUrl);

  const parsedDsvg = useMemo(() => (dsvg ? parseDsvg(dsvg) : null), [dsvg]);
  const renderer = useMemo(() => (dsvg ? new DiplicityMap(dsvg) : null), [dsvg]);

  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(true);
  const [containerDimensions, setContainerDimensions] = useState<
    Dimensions | undefined
  >(undefined);

  const {
    variant,
    phase,
    orders,
    selected,
    highlighted,
    civilDisorderNations,
  } = interactiveMapProps;

  const renderState = useMemo(
    () =>
      toRenderState(
        variant,
        phase,
        orders ?? [],
        selected,
        highlighted ?? [],
        civilDisorderNations ?? []
      ),
    [variant, phase, orders, selected, highlighted, civilDisorderNations]
  );

  const mapViewBox = parsedDsvg?.viewBox;

  const containerAspectRatio =
    containerDimensions?.width && containerDimensions?.height
      ? containerDimensions.width / containerDimensions.height
      : undefined;

  const svgAspectRatio =
    mapViewBox?.width && mapViewBox?.height
      ? mapViewBox.width / mapViewBox.height
      : undefined;

  const containerIsTallerThanSvg =
    containerAspectRatio && svgAspectRatio
      ? containerAspectRatio < svgAspectRatio
      : undefined;

  const containerIsWiderThanSvg =
    containerAspectRatio && svgAspectRatio
      ? containerAspectRatio > svgAspectRatio
      : undefined;

  const calculateFittedScale = (): number => {
    if (!containerDimensions || !mapViewBox) return 1;
    if (containerIsTallerThanSvg) {
      return containerDimensions.height / mapViewBox.height;
    }
    if (containerIsWiderThanSvg) {
      return containerDimensions.width / mapViewBox.width;
    }
    return 1;
  };

  const calculateContainedScale = (): number => {
    if (!containerDimensions || !mapViewBox) return 1;
    const scaleX = containerDimensions.width / mapViewBox.width;
    const scaleY = containerDimensions.height / mapViewBox.height;
    return Math.min(scaleX, scaleY);
  };

  const fittedScale = calculateFittedScale();
  const containedScale = calculateContainedScale();
  const minScale = isFullscreen ? fittedScale : containedScale;

  const syncViewBox = (state: TransformState) => {
    const container = containerSizeRef.current;
    if (!container || !mapViewBox) return;
    applyViewBox(
      mapVisualRef.current,
      transformToViewBox(state, container, mapViewBox)
    );
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen((prev) => {
      const newIsFullscreen = !prev;
      if (transformRef.current && containerDimensions && mapViewBox) {
        const targetScale = newIsFullscreen ? fittedScale : containedScale;
        const scaledWidth = mapViewBox.width * targetScale;
        const scaledHeight = mapViewBox.height * targetScale;
        const centerX = (containerDimensions.width - scaledWidth) / 2;
        const centerY = (containerDimensions.height - scaledHeight) / 2;
        transformRef.current.setTransform(centerX, centerY, targetScale, 300);
      }
      return newIsFullscreen;
    });
  };

  const handleGestureStart = () => {
    if (hitRef.current) {
      hitRef.current.style.pointerEvents = "none";
    }
  };

  const handleGestureStop = () => {
    if (hitRef.current) {
      hitRef.current.style.pointerEvents = "";
    }
  };

  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        containerSizeRef.current = { width, height };
        setContainerDimensions({ width, height });
      }
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // Seed the visible layer's viewBox before first paint so it isn't briefly
  // rendered without a coordinate system; the transform sync refines it.
  useLayoutEffect(() => {
    if (mapViewBox) {
      applyViewBox(mapVisualRef.current, mapViewBox);
    }
  }, [mapViewBox]);

  useEffect(() => {
    if (transformRef.current && containerDimensions && mapViewBox) {
      const scaledWidth = mapViewBox.width * minScale;
      const scaledHeight = mapViewBox.height * minScale;
      const centerX = (containerDimensions.width - scaledWidth) / 2;
      const centerY = (containerDimensions.height - scaledHeight) / 2;
      transformRef.current.setTransform(centerX, centerY, minScale, 0);
    }
  }, [minScale, containerDimensions, mapViewBox]);

  if (isLoading || !parsedDsvg || !renderer) {
    return (
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%", position: "relative" }}
        className="flex items-center justify-center"
      ></div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", position: "relative" }}
    >
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
          maxScale={4}
          minScale={minScale}
          centerOnInit={true}
          limitToBounds={true}
          centerZoomedOut={true}
          disablePadding={true}
          panning={{ velocityDisabled: true }}
          velocityAnimation={{ disabled: true }}
          onTransformed={(_ref, state) => syncViewBox(state)}
          onPanningStart={handleGestureStart}
          onPanningStop={handleGestureStop}
          onPinchingStart={handleGestureStart}
          onPinchingStop={handleGestureStop}
          onZoomStart={handleGestureStart}
          onZoomStop={handleGestureStop}
        >
          <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
            <MapHitLayer
              svgRef={hitRef}
              parsedDsvg={parsedDsvg}
              interactive={interactiveMapProps.interactive}
              isNative={isNative}
              renderableProvinces={interactiveMapProps.renderableProvinces}
              onHover={setHoveredProvince}
              onClickProvince={interactiveMapProps.onClickProvince}
            />
          </TransformComponent>
        </TransformWrapper>
      </div>
      <Button
        size="icon"
        onClick={handleToggleFullscreen}
        className="absolute bottom-5 right-5 rounded-full shadow-lg"
      >
        {isFullscreen ? <Minimize /> : <Maximize />}
      </Button>
    </div>
  );
};

export { InteractiveMapZoomWrapper };
