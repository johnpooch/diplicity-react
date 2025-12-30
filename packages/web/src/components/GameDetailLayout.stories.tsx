import type { Meta, StoryObj } from "@storybook/react";
import { GameDetailLayout } from "./GameDetailLayout";
import { Navigation } from "./Navigation";
import { AppBar } from "./AppBar.new";
import { Button } from "@/components/ui/button";
import { Icon, IconName } from "./Icon";
import { homeNavigationItems } from "../navigation/navigationItems";
import { GameCard } from "./GameCard.new";
import { InfoPanel } from "./InfoPanel.new";

const meta = {
  title: "Layout/GameDetailLayout",
  component: GameDetailLayout,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof GameDetailLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

const MapComponent = () => (
  <svg viewBox="0 0 800 600" style={{ width: "100%", height: "100%" }}>
    <defs>
      <pattern
        id="horizontalStripes"
        width="20"
        height="20"
        patternUnits="userSpaceOnUse"
      >
        <rect width="20" height="10" fill="#e2e8f0" />
        <rect y="10" width="20" height="10" fill="#cbd5e1" />
      </pattern>
    </defs>
    <rect width="800" height="600" fill="url(#horizontalStripes)" />
    <text
      x="400"
      y="300"
      fontSize="48"
      fill="#64748b"
      textAnchor="middle"
      dominantBaseline="middle"
    >
      Map
    </text>
  </svg>
);

export const Default: Story = {
  args: {
    children: <div>Hello</div>,
  },
};

export const WithPanelOpen: Story = {
  args: {
    children: <div className="p-4">Hello World</div>,
    isPanelOpen: true,
  },
};
