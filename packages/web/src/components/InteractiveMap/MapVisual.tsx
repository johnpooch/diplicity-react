import React, { useMemo } from "react";
import type { ParsedDsvg } from "./dsvgParser";
import type { DiplicityMap, RenderState } from "./mapRenderer";
import {
  HOVER_FILL,
  HOVER_STROKE_COLOR,
  HOVER_STROKE_WIDTH,
  splitAfterProvinceFills,
  stripSvgWrapper,
} from "./mapLayers";

type MapVisualProps = {
  parsedDsvg: ParsedDsvg;
  renderer: DiplicityMap;
  renderState: RenderState;
  hoveredProvince: string | null;
  selected: string[];
  svgRef: React.Ref<SVGSVGElement>;
};

// Viewport-filling visual layer; viewBox is mutated imperatively (not via JSX) so React doesn't clobber gesture updates.
const MapVisual: React.FC<MapVisualProps> = ({
  parsedDsvg,
  renderer,
  renderState,
  hoveredProvince,
  selected,
  svgRef,
}) => {
  const { provincePaths, namedCoastPaths } = parsedDsvg;

  const renderedSplit = useMemo(
    () => splitAfterProvinceFills(stripSvgWrapper(renderer.render(renderState))),
    [renderer, renderState]
  );

  const hoveredPath = hoveredProvince
    ? (provincePaths.get(hoveredProvince) ??
      namedCoastPaths.get(hoveredProvince))
    : undefined;
  const hoveredIsSelected =
    hoveredProvince !== null && selected.includes(hoveredProvince);

  return (
    <svg
      ref={svgRef}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
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
    </svg>
  );
};

MapVisual.displayName = "MapVisual";

export { MapVisual };
