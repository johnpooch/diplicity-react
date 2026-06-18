import type { Meta, StoryObj } from "@storybook/react";
import { useMemo, useRef, useEffect } from "react";
import { MapVisual } from "./MapVisual";
import { parseDsvg } from "./dsvgParser";
import { DiplicityMap } from "./mapRenderer";
import { toRenderState } from "./toRenderState";
import { viewBoxToString } from "./viewBoxZoom";
import CLASSICAL_DSVG from "./classicalMap.dsvg?raw";
import {
  mockNations,
  mockPhaseMovement,
  mockOrders,
} from "../../mocks/legacy";

const variant = {
  id: "Classical",
  nations: mockNations,
};

const MapStory: React.FC<{
  selected?: string[];
  highlighted?: string[];
}> = ({ selected = [], highlighted = [] }) => {
  const parsedDsvg = useMemo(() => parseDsvg(CLASSICAL_DSVG), []);
  const renderer = useMemo(() => new DiplicityMap(CLASSICAL_DSVG), []);
  const renderState = useMemo(
    () =>
      toRenderState(variant, mockPhaseMovement, mockOrders, selected, highlighted, []),
    [selected, highlighted]
  );
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (svgRef.current) {
      svgRef.current.setAttribute("viewBox", viewBoxToString(parsedDsvg.viewBox));
    }
  }, [parsedDsvg]);

  return (
    <div style={{ width: 800, height: 600, position: "relative" }}>
      <MapVisual
        svgRef={svgRef}
        parsedDsvg={parsedDsvg}
        renderer={renderer}
        renderState={renderState}
        hoveredProvince={null}
        selected={selected}
      />
    </div>
  );
};

export default {
  title: "Components/InteractiveMap",
  component: MapVisual,
} as Meta;

type Story = StoryObj;

export const Default: Story = { render: () => <MapStory /> };

export const WithSelection: Story = {
  render: () => <MapStory selected={["lon"]} />,
};

export const WithHighlights: Story = {
  render: () => <MapStory highlighted={["par", "bre", "mar"]} />,
};
