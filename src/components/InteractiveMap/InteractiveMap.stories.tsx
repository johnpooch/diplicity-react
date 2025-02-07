import { Meta, StoryObj } from "@storybook/react";
import { InteractiveMap } from "./InteractiveMap";
import classical from "../../data/map/classical.json";

export default {
  title: "Components/InteractiveMap",
  component: InteractiveMap,
  args: {
    map: classical,
  },
} as Meta;

type Story = StoryObj<typeof InteractiveMap>;

export const Default: Story = {};
