import { Meta, StoryObj } from "@storybook/react";
import { useMemo } from "react";
import { InteractiveMap } from "./InteractiveMap";
import { parseDsvg } from "./dsvgParser";
import { DiplicityMap } from "./mapRenderer";
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

const StoryWrapper: React.FC<{
  selected?: string[];
  highlighted?: string[];
  renderableProvinces?: string[];
}> = ({ selected = [], highlighted = [], renderableProvinces }) => {
  const parsedDsvg = useMemo(() => parseDsvg(CLASSICAL_DSVG), []);
  const renderer = useMemo(() => new DiplicityMap(CLASSICAL_DSVG), []);

  return (
    <InteractiveMap
      interactive
      variant={variant}
      phase={mockPhaseMovement}
      orders={mockOrders}
      selected={selected}
      highlighted={highlighted}
      renderableProvinces={renderableProvinces}
      parsedDsvg={parsedDsvg}
      renderer={renderer}
      onClickProvince={(id) => console.log("clicked", id)}
    />
  );
};

export default {
  title: "Components/InteractiveMap",
  component: InteractiveMap,
  render: (args) => <StoryWrapper {...args} />,
} as Meta<typeof StoryWrapper>;

type Story = StoryObj<typeof StoryWrapper>;

export const Default: Story = {};

export const WithSelection: Story = {
  args: {
    selected: ["lon"],
  },
};

export const WithHighlights: Story = {
  args: {
    highlighted: ["par", "bre", "mar"],
  },
};
