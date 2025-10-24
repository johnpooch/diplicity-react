import { Meta, StoryObj } from "@storybook/react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { useRef, useEffect, useState, CSSProperties, forwardRef } from "react";

type StoryArgs = {
  width: number;
  height: number;
};

type Dimensions = {
  width: number;
  height: number;
};

const SvgComponent = ({
  svgRef,
}: {
  svgRef: React.RefObject<SVGSVGElement>;
}) => {
  return (
    <svg ref={svgRef} width="600" height="400" viewBox="0 0 600 400">
      <defs>
        <pattern
          id="diagonalLines"
          patternUnits="userSpaceOnUse"
          width="20"
          height="20"
        >
          <path d="M0,20 L20,0" stroke="navy" strokeWidth="2" fill="none" />
        </pattern>
      </defs>
      <rect
        x="0"
        y="0"
        width="600"
        height="400"
        fill="lightblue"
        stroke="navy"
        strokeWidth="4"
      />
      <rect x="0" y="0" width="600" height="400" fill="url(#diagonalLines)" />
    </svg>
  );
};

const ContainerComponent = forwardRef<
  HTMLDivElement,
  {
    children: React.ReactNode;
    style: CSSProperties;
  }
>(({ children, style }, ref) => {
  return (
    <div ref={ref} style={{ border: "1px solid #ccc", ...style }}>
      {children}
    </div>
  );
});

const TransformWrapperStory = ({
  width,
  height,
}: {
  width: number;
  height: number;
}) => {
  const [svgViewBox, setSvgViewBox] = useState<Dimensions | undefined>(
    undefined
  );
  const [containerDimensions, setContainerDimensions] = useState<
    Dimensions | undefined
  >(undefined);

  const svgRef = useRef<SVGSVGElement>(null);
  const transformRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Calculate scale based on the limiting dimension
  const calculateScale = (): number => {
    if (!containerDimensions || !svgViewBox) return 1;

    if (containerIsTallerThanSvg) {
      return containerDimensions.height / svgViewBox.height;
    }

    if (containerIsWiderThanSvg) {
      return containerDimensions.width / svgViewBox.width;
    }

    return 1;
  };

  const scale = calculateScale();

  // Initialize container dimensions
  useEffect(() => {
    if (!containerRef.current) return;
    setContainerDimensions({
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });
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
    if (transformRef.current) {
      transformRef.current.setTransform(0, 0, scale, 0);
    }
  }, [scale]);

  return (
    <ContainerComponent ref={containerRef} style={{ width, height }}>
      <TransformWrapper
        ref={transformRef}
        maxScale={4}
        centerOnInit={true}
        minScale={scale}
      >
        <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
          <SvgComponent svgRef={svgRef} />
        </TransformComponent>
      </TransformWrapper>
    </ContainerComponent>
  );
};

export default {
  title: "Components/TransformWrapper",
  component: TransformWrapperStory,
  render: args => <TransformWrapperStory {...args} />,
} as Meta<StoryArgs>;

type Story = StoryObj<typeof TransformWrapperStory>;

export const Tall: Story = {
  args: {
    width: 300,
    height: 700,
  },
};

export const Wide: Story = {
  args: {
    width: 700,
    height: 300,
  },
};
