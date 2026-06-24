import React, { useMemo, useRef, useState } from "react";
import type {
  Order,
  PhaseRetrieve,
  Variant,
} from "../../api/generated/endpoints";
import type { ParsedDsvg } from "./dsvgParser";
import type { DiplicityMap, RenderState } from "./mapRenderer";
import { toRenderState } from "./toRenderState";
import { recordInitialRender } from "./mapTelemetry";
import { isNativePlatform } from "../../utils/platform";

type VariantForMap = Pick<Variant, "id" | "nations">;

type InteractiveMapProps = {
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
  style?: React.CSSProperties;
  ref?: React.Ref<SVGSVGElement>;
  parsedDsvg: ParsedDsvg;
  renderer: DiplicityMap;
};

const HOVER_STROKE_WIDTH = 5;
const HOVER_STROKE_COLOR = "white";
const HOVER_FILL = "rgba(255, 255, 255, 0.6)";

const stripSvgWrapper = (svg: string): string => {
  const openEnd = svg.indexOf(">");
  const closeStart = svg.lastIndexOf("</svg>");
  if (openEnd === -1 || closeStart === -1) {
    return svg;
  }
  return svg.slice(openEnd + 1, closeStart).trim();
};

const ABOVE_HOVER_LAYER_IDS = [
  "supply-center-markers",
  "province-names",
  "borders",
  "foreground",
  "units",
  "orders",
];

const splitAfterProvinceFills = (
  inner: string
): { below: string; above: string } => {
  const candidates = ABOVE_HOVER_LAYER_IDS.map((id) =>
    inner.indexOf(`<g id="${id}">`)
  ).filter((index) => index !== -1);
  if (candidates.length === 0) {
    return { below: inner, above: "" };
  }
  const splitIndex = Math.min(...candidates);
  return {
    below: inner.slice(0, splitIndex),
    above: inner.slice(splitIndex),
  };
};

const InteractiveMap: React.FC<InteractiveMapProps> = (props) => {
  const isNative = isNativePlatform();
  const [hoveredProvince, setHoveredProvince] = useState<string | null>(null);

  const initialRenderRecordedRef = useRef(false);

  const orders = useMemo(() => props.orders ?? [], [props.orders]);
  const highlighted = useMemo(
    () => props.highlighted ?? [],
    [props.highlighted]
  );
  const civilDisorderNations = useMemo(
    () => props.civilDisorderNations ?? [],
    [props.civilDisorderNations]
  );

  const renderState = useMemo<RenderState>(
    () =>
      toRenderState(
        props.variant,
        props.phase,
        orders,
        props.selected,
        highlighted,
        civilDisorderNations
      ),
    [props.variant, props.phase, orders, props.selected, highlighted, civilDisorderNations]
  );

  const renderedSplit = useMemo(
    () => {
      const t0 = performance.now();
      const result = splitAfterProvinceFills(
        stripSvgWrapper(props.renderer.render(renderState))
      );
      if (!initialRenderRecordedRef.current) {
        initialRenderRecordedRef.current = true;
        recordInitialRender({
          variantId: props.variant.id,
          renderMs: performance.now() - t0,
        });
      }
      return result;
    },
    [props.renderer, renderState, props.variant.id]
  );

  const { viewBox, provincePaths, namedCoastPaths } = props.parsedDsvg;

  const allHitPaths = useMemo(
    () => [
      ...Array.from(provincePaths.entries()),
      ...Array.from(namedCoastPaths.entries()),
    ],
    [provincePaths, namedCoastPaths]
  );

  const renderableSet = useMemo(
    () =>
      new Set(
        props.renderableProvinces ?? [
          ...provincePaths.keys(),
          ...namedCoastPaths.keys(),
        ]
      ),
    [props.renderableProvinces, provincePaths, namedCoastPaths]
  );

  const handlePointerEnter = (
    id: string,
    event: React.PointerEvent<SVGPathElement>
  ) => {
    if (event.pointerType === "mouse" && props.interactive && !isNative) {
      setHoveredProvince(id);
    }
  };

  const handlePointerLeave = (event: React.PointerEvent<SVGPathElement>) => {
    if (event.pointerType === "mouse" && props.interactive) {
      setHoveredProvince(null);
    }
  };

  const handleClick = (
    id: string,
    event: React.MouseEvent<SVGPathElement>
  ) => {
    if (props.interactive) {
      props.onClickProvince?.(id, event);
    }
  };

  const svgStyle: React.CSSProperties = {
    width: props.style?.width ?? viewBox.width,
    height: props.style?.height ?? viewBox.height,
    display: "block",
    transform: "translateZ(0)",
    ...props.style,
  };

  const hoveredPath = hoveredProvince
    ? (provincePaths.get(hoveredProvince) ??
      namedCoastPaths.get(hoveredProvince))
    : undefined;
  const hoveredIsSelected =
    hoveredProvince !== null && props.selected.includes(hoveredProvince);

  return (
    <svg
      ref={props.ref}
      style={svgStyle}
      viewBox={`${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <g dangerouslySetInnerHTML={{ __html: renderedSplit.below }} />
      {hoveredPath && (
        <g>
          <path
            d={hoveredPath}
            fill={hoveredIsSelected ? "none" : HOVER_FILL}
            stroke={HOVER_STROKE_COLOR}
            strokeWidth={HOVER_STROKE_WIDTH}
            pointerEvents="none"
          />
        </g>
      )}
      {renderedSplit.above && (
        <g dangerouslySetInnerHTML={{ __html: renderedSplit.above }} />
      )}
      <g>
        {allHitPaths.map(([id, d]) => {
          const enabled = renderableSet.has(id);
          return (
            <path
              key={id}
              id={id}
              d={d}
              fill="transparent"
              stroke="none"
              style={{
                cursor: enabled && props.interactive ? "pointer" : "default",
              }}
              pointerEvents={enabled ? "visiblePainted" : "none"}
              onPointerEnter={(event) => handlePointerEnter(id, event)}
              onPointerLeave={handlePointerLeave}
              onClick={(event) => handleClick(id, event)}
            />
          );
        })}
      </g>
    </svg>
  );
};

InteractiveMap.displayName = "InteractiveMap";

export { InteractiveMap };
