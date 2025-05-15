import { Meta, StoryObj } from "@storybook/react";
import { Cross } from "./cross";

export default {
  title: "Components/Shapes/Cross",
  component: Cross,
  args: {
    x: 50,
    y: 50,
    width: 10,
    length: 50,
    angle: 45,
    fill: "blue",
    stroke: "red",
    strokeWidth: 2,
  },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  render: (args: any) => (
    <svg width="400" height="400">
      <Cross {...args} />
      {/* Draw a dot represnting x,y */}
      <circle cx={args.x} cy={args.y} r={2} fill="black" />
      <text x={args.x} y={args.y} dx={20}>
        x,y
      </text>
    </svg>
  ),
} as Meta;

type Story = StoryObj<typeof Cross>;

export const Default: Story = {};
