import {
  TransformWrapper,
  TransformComponent,
  ReactZoomPanPinchContentRef,
} from "react-zoom-pan-pinch";
import { useRef, useState, useEffect, useMemo } from "react";
import { Maximize, Minimize } from "lucide-react";
import { Button } from "@/components/ui/button";

import { InteractiveMap } from "./InteractiveMap";
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

  // --- Diagnostic ---
  const renderCountRef = useRef(0);
  const prevZoomPropsRef = useRef<typeof interactiveMapProps | null>(null);
  const lastTransformTimeRef = useRef<number | null>(null);
  const transformFrameTimesRef = useRef<number[]>([]);
  const fpsFlushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  const handleGestureStart = () => {
    if (svgRef.current) {
      svgRef.current.style.pointerEvents = "none";
    }
  };

  const handleGestureStop = () => {
    if (svgRef.current) {
      svgRef.current.style.pointerEvents = "";
    }
  };

  const handleTransformed = () => {
    const now = performance.now();
    if (lastTransformTimeRef.current !== null) {
      transformFrameTimesRef.current.push(now - lastTransformTimeRef.current);
    }
    lastTransformTimeRef.current = now;

    if (fpsFlushTimerRef.current) clearTimeout(fpsFlushTimerRef.current);
    fpsFlushTimerRef.current = setTimeout(() => {
      const times = transformFrameTimesRef.current;
      if (times.length > 1) {
        const avg = times.reduce((a, b) => a + b, 0) / times.length;
        console.log(
          `[InteractiveMapZoom] gesture: ${times.length} updates, avg ${avg.toFixed(1)}ms between transforms (~${(1000 / avg).toFixed(0)} fps)`
        );
      }
      transformFrameTimesRef.current = [];
      lastTransformTimeRef.current = null;
    }, 500);
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

  // --- Diagnostic logging ---
  renderCountRef.current += 1;
  if (prevZoomPropsRef.current) {
    const changed = (
      Object.keys(interactiveMapProps) as Array<keyof typeof interactiveMapProps>
    ).filter((k) => interactiveMapProps[k] !== prevZoomPropsRef.current![k]);
    console.log(
      `[InteractiveMapZoom] render #${renderCountRef.current}`,
      changed.length > 0 ? { changedProps: changed } : "(internal state change)"
    );
  } else {
    console.log(`[InteractiveMapZoom] render #${renderCountRef.current} (initial)`);
  }
  prevZoomPropsRef.current = interactiveMapProps;

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
        onPanningStart={handleGestureStart}
        onPanningStop={handleGestureStop}
        onPinchingStart={handleGestureStart}
        onPinchingStop={handleGestureStop}
        onZoomStart={handleGestureStart}
        onZoomStop={handleGestureStop}
      >
        <TransformComponent
          wrapperStyle={{ width: "100%", height: "100%" }}
          contentStyle={{ willChange: "transform" }}
        >
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
