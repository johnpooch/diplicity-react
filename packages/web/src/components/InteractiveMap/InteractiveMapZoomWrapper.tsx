import {
  TransformWrapper,
  TransformComponent,
  ReactZoomPanPinchContentRef,
} from "react-zoom-pan-pinch";
import { useRef, useState, useEffect, useMemo } from "react";
import { Maximize, Minimize } from "lucide-react";
import { Button } from "@/components/ui/button";

import { InteractiveMap } from "./InteractiveMap";
import { recordGesture, type GestureType } from "./mapTelemetry";
import { useDsvg } from "../../hooks/useDsvg";
import { parseDsvg } from "./dsvgParser";
import { DiplicityMap } from "./mapRenderer";
import type { Variant } from "../../api/generated/endpoints";

type VariantForMap = Pick<Variant, "id" | "nations" | "svgUrl">;

type InteractiveMapProps = Omit<
  React.ComponentProps<typeof InteractiveMap>,
  "parsedDsvg" | "renderer" | "variant"
> & {
  variant: VariantForMap;
};

type Dimensions = {
  width: number;
  height: number;
};

type InteractiveMapZoomWrapperProps = {
  interactiveMapProps: InteractiveMapProps;
};

const InteractiveMapZoomWrapper: React.FC<InteractiveMapZoomWrapperProps> = ({
  interactiveMapProps,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const transformRef = useRef<ReactZoomPanPinchContentRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const lastTransformTimeRef = useRef<number | null>(null);
  const transformFrameTimesRef = useRef<number[]>([]);
  const gestureTypeRef = useRef<GestureType | null>(null);
  const gestureStartTimeRef = useRef<number>(0);

  const { data: dsvg, isLoading } = useDsvg(interactiveMapProps.variant.svgUrl);

  const parsedDsvg = useMemo(() => (dsvg ? parseDsvg(dsvg) : null), [dsvg]);
  const renderer = useMemo(
    () => (dsvg ? new DiplicityMap(dsvg) : null),
    [dsvg]
  );

  const [isFullscreen, setIsFullscreen] = useState(true);

  const [svgViewBox, setSvgViewBox] = useState<Dimensions | undefined>(
    undefined
  );

  const [containerDimensions, setContainerDimensions] = useState<
    Dimensions | undefined
  >(undefined);

  const containerAspectRatio =
    containerDimensions?.width && containerDimensions?.height
      ? containerDimensions.width / containerDimensions.height
      : undefined;

  const svgAspectRatio =
    svgViewBox?.width && svgViewBox?.height
      ? svgViewBox.width / svgViewBox.height
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
    if (!containerDimensions || !svgViewBox) return 1;

    if (containerIsTallerThanSvg) {
      return containerDimensions.height / svgViewBox.height;
    }

    if (containerIsWiderThanSvg) {
      return containerDimensions.width / svgViewBox.width;
    }

    return 1;
  };

  const calculateContainedScale = (): number => {
    if (!containerDimensions || !svgViewBox) return 1;

    const scaleX = containerDimensions.width / svgViewBox.width;
    const scaleY = containerDimensions.height / svgViewBox.height;

    return Math.min(scaleX, scaleY);
  };

  const fittedScale = calculateFittedScale();
  const containedScale = calculateContainedScale();

  const minScale = isFullscreen ? fittedScale : containedScale;

  const handleToggleFullscreen = () => {
    setIsFullscreen((prev) => {
      const newIsFullscreen = !prev;

      if (transformRef.current && containerDimensions && svgViewBox) {
        const targetScale = newIsFullscreen ? fittedScale : containedScale;

        const scaledWidth = svgViewBox.width * targetScale;
        const scaledHeight = svgViewBox.height * targetScale;
        const centerX = (containerDimensions.width - scaledWidth) / 2;
        const centerY = (containerDimensions.height - scaledHeight) / 2;

        transformRef.current.setTransform(centerX, centerY, targetScale, 300);
      }

      return newIsFullscreen;
    });
  };

  const handleGestureStart = (gestureType: GestureType) => {
    if (svgRef.current) {
      svgRef.current.style.pointerEvents = "none";
    }
    gestureTypeRef.current = gestureType;
    gestureStartTimeRef.current = performance.now();
    transformFrameTimesRef.current = [];
    lastTransformTimeRef.current = null;
  };

  const handleGestureStop = () => {
    if (svgRef.current) {
      svgRef.current.style.pointerEvents = "";
    }
    if (gestureTypeRef.current !== null) {
      recordGesture({
        variantId: interactiveMapProps.variant.id,
        gestureType: gestureTypeRef.current,
        durationMs: performance.now() - gestureStartTimeRef.current,
        frameMs: transformFrameTimesRef.current,
        implementation: "svg",
      });
      gestureTypeRef.current = null;
    }
    transformFrameTimesRef.current = [];
    lastTransformTimeRef.current = null;
  };

  const handleTransformed = () => {
    const now = performance.now();
    if (lastTransformTimeRef.current !== null) {
      transformFrameTimesRef.current.push(now - lastTransformTimeRef.current);
    }
    lastTransformTimeRef.current = now;
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setContainerDimensions({ width, height });
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    if (parsedDsvg) {
      setSvgViewBox({
        width: parsedDsvg.viewBox.width,
        height: parsedDsvg.viewBox.height,
      });
    }
  }, [parsedDsvg]);

  useEffect(() => {
    if (transformRef.current && containerDimensions && svgViewBox) {
      const scaledWidth = svgViewBox.width * minScale;
      const scaledHeight = svgViewBox.height * minScale;
      const centerX = (containerDimensions.width - scaledWidth) / 2;
      const centerY = (containerDimensions.height - scaledHeight) / 2;
      transformRef.current.setTransform(centerX, centerY, minScale, 0);
    }
  }, [minScale, containerDimensions, svgViewBox]);

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
        onTransformed={handleTransformed}
        onPanningStart={() => handleGestureStart("pan")}
        onPanningStop={handleGestureStop}
        onPinchingStart={() => handleGestureStart("pinch")}
        onPinchingStop={handleGestureStop}
        onZoomStart={() => handleGestureStart("zoom")}
        onZoomStop={handleGestureStop}
      >
        <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
          <InteractiveMap
            ref={svgRef}
            {...interactiveMapProps}
            parsedDsvg={parsedDsvg}
            renderer={renderer}
          />
        </TransformComponent>
      </TransformWrapper>
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
