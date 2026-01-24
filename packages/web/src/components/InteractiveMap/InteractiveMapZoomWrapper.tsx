import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { useRef, useState, useEffect } from "react";
import { Maximize, Minimize } from "lucide-react";
import { Button } from "@/components/ui/button";

import { InteractiveMap } from "./InteractiveMap";

type InteractiveMapProps = React.ComponentProps<typeof InteractiveMap>;

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
  const transformRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [isFullscreen, setIsFullscreen] = useState(true);

  const [svgViewBox, setSvgViewBox] = useState<Dimensions | undefined>(
    undefined
  );

  const [containerDimensions, setContainerDimensions] = useState<
    Dimensions | undefined
  >(undefined);

  // Calculate aspect ratios with null safety
  const containerAspectRatio =
    containerDimensions?.width && containerDimensions?.height
      ? containerDimensions.width / containerDimensions.height
      : undefined;

  const svgAspectRatio =
    svgViewBox?.width && svgViewBox?.height
      ? svgViewBox.width / svgViewBox.height
      : undefined;

  // Determine which dimension is the limiting factor
  const containerIsTallerThanSvg =
    containerAspectRatio && svgAspectRatio
      ? containerAspectRatio < svgAspectRatio
      : undefined;

  const containerIsWiderThanSvg =
    containerAspectRatio && svgAspectRatio
      ? containerAspectRatio > svgAspectRatio
      : undefined;

  // Calculate scale based on the limiting dimension (fitted/fullscreen mode)
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

  // Calculate scale for contained mode (entire map visible with padding)
  const calculateContainedScale = (): number => {
    if (!containerDimensions || !svgViewBox) return 1;

    // Always use the smaller scale to ensure entire map fits
    const scaleX = containerDimensions.width / svgViewBox.width;
    const scaleY = containerDimensions.height / svgViewBox.height;

    return Math.min(scaleX, scaleY);
  };

  const fittedScale = calculateFittedScale();
  const containedScale = calculateContainedScale();

  // Use appropriate scale based on fullscreen mode
  const minScale = isFullscreen ? fittedScale : containedScale;

  // Handle toggling between fullscreen and contained modes
  const handleToggleFullscreen = () => {
    setIsFullscreen(prev => {
      const newIsFullscreen = !prev;

      // When switching modes, reset the transform to the appropriate scale
      if (transformRef.current && containerDimensions && svgViewBox) {
        const targetScale = newIsFullscreen ? fittedScale : containedScale;

        // Calculate centered position
        const scaledWidth = svgViewBox.width * targetScale;
        const scaledHeight = svgViewBox.height * targetScale;
        const centerX = (containerDimensions.width - scaledWidth) / 2;
        const centerY = (containerDimensions.height - scaledHeight) / 2;

        // Animate the transition with setTransform(x, y, scale, animationTime)
        transformRef.current.setTransform(centerX, centerY, targetScale, 300);
      }

      return newIsFullscreen;
    });
  };

  // Initialize container dimensions and observe resize
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver(entries => {
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

  // Initialize SVG viewBox dimensions
  useEffect(() => {
    setSvgViewBox({
      width: svgRef.current?.viewBox.baseVal.width || 0,
      height: svgRef.current?.viewBox.baseVal.height || 0,
    });
  }, []);

  // Apply scale transformation when scale value changes
  useEffect(() => {
    if (transformRef.current && containerDimensions && svgViewBox) {
      // Calculate centered position
      const scaledWidth = svgViewBox.width * minScale;
      const scaledHeight = svgViewBox.height * minScale;
      const centerX = (containerDimensions.width - scaledWidth) / 2;
      const centerY = (containerDimensions.height - scaledHeight) / 2;

      transformRef.current.setTransform(centerX, centerY, minScale, 0);
    }
  }, [minScale, containerDimensions, svgViewBox]);

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
      >
        <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
          <InteractiveMap ref={svgRef} {...interactiveMapProps} />
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
