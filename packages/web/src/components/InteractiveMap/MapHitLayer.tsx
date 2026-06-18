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

// Transparent hit-path layer that RZPP CSS-transforms; geometry-based hit-testing works at any scale.
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
