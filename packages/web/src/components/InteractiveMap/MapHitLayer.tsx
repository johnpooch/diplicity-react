import React, { useMemo } from "react";
import type { ParsedDsvg } from "./dsvgParser";

type MapHitLayerProps = {
  parsedDsvg: ParsedDsvg;
  interactive?: boolean;
  isNative: boolean;
  renderableProvinces?: string[];
  onHover: (province: string | null) => void;
  onClickProvince?: (
    province: string,
    event: React.MouseEvent<SVGPathElement>
  ) => void;
  svgRef: React.Ref<SVGSVGElement>;
};

// Transparent, intrinsic-sized SVG holding only the province hit paths. This is
// the element react-zoom-pan-pinch CSS-transforms for pan/zoom: because every
// path is transparent, re-rasterising it at any scale costs nothing and never
// flickers, while pointer hit-testing (which uses geometry, not the raster)
// continues to work at all zoom levels. Province hover/click is reported up to
// the wrapper, which drives the visible MapVisual layer.
const MapHitLayer: React.FC<MapHitLayerProps> = ({
  parsedDsvg,
  interactive,
  isNative,
  renderableProvinces,
  onHover,
  onClickProvince,
  svgRef,
}) => {
  const { viewBox, provincePaths, namedCoastPaths } = parsedDsvg;

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
        renderableProvinces ?? [
          ...provincePaths.keys(),
          ...namedCoastPaths.keys(),
        ]
      ),
    [renderableProvinces, provincePaths, namedCoastPaths]
  );

  return (
    <svg
      ref={svgRef}
      style={{ width: viewBox.width, height: viewBox.height, display: "block" }}
      viewBox={`${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`}
      preserveAspectRatio="xMidYMid meet"
    >
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
              style={{ cursor: enabled && interactive ? "pointer" : "default" }}
              pointerEvents={enabled ? "visiblePainted" : "none"}
              onPointerEnter={(event) => {
                if (event.pointerType === "mouse" && interactive && !isNative) {
                  onHover(id);
                }
              }}
              onPointerLeave={(event) => {
                if (event.pointerType === "mouse" && interactive) {
                  onHover(null);
                }
              }}
              onClick={(event) => {
                if (interactive) {
                  onClickProvince?.(id, event);
                }
              }}
            />
          );
        })}
      </g>
    </svg>
  );
};

MapHitLayer.displayName = "MapHitLayer";

export { MapHitLayer };
