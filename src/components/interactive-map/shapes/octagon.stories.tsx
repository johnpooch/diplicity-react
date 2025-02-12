import { Meta, StoryObj } from "@storybook/react";
import { Octagon } from "./octagon";
import { Cross } from "./cross";

export default {
  title: "Components/Shapes/Octagon",
  component: Octagon,
  args: {
    x: 100,
    y: 100,
    size: 50,
    fill: "transparent",
    stroke: "black",
    strokeWidth: 8,
  },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  render: (args: any) => (
    <svg width="400" height="400">
      <Octagon {...args} />
      {/* Draw a dot representing x,y */}
      <circle cx={args.x} cy={args.y} r={2} fill="black" />
      <text x={args.x} y={args.y} dx={20}>
        x,y
      </text>
    </svg>
  ),
} as Meta;

type Story = StoryObj<typeof Octagon>;

export const Default: Story = {};

export const Failed: Story = {
  args: {
    onRenderBottomCenter: (x: number, y: number) => {
      return (
        <Cross
          x={x}
          y={y}
          width={5}
          length={20}
          angle={45}
          fill="blue"
          stroke="red"
          strokeWidth={2}
        />
      );
    },
  },
};
