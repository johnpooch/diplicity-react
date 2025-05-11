import { Meta, StoryObj } from "@storybook/react";
import { CurvedArrow } from "./curved-arrow";
import { Cross } from "./cross";

export default {
  title: "Components/Shapes/CurvedArrow",
  component: CurvedArrow,
  args: {
    x1: 50,
    y1: 50,
    x2: 200,
    y2: 200,
    x3: 350,
    y3: 50,
    lineWidth: 5,
    fill: "blue",
    stroke: "red",
    strokeWidth: 2,
    offset: 50,
    arrowWidth: 7.5,
    arrowLength: 10,
  },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  render: (args: any) => (
    <svg width="400" height="400">
      <circle cx={args.x1} cy={args.y1} r={5} fill="black" />
      <text x={args.x1} y={args.y1} dx={10} dy={-10}>
        x1,y1
      </text>
      <circle cx={args.x2} cy={args.y2} r={5} fill="black" />
      <text x={args.x2} y={args.y2} dx={10} dy={-10}>
        x2,y2
      </text>
      <circle cx={args.x3} cy={args.y3} r={5} fill="black" />
      <text x={args.x3} y={args.y3} dx={10} dy={-10}>
        x3,y3
      </text>
      <circle
        cx={args.x1}
        cy={args.y1}
        r={args.offset}
        fill="none"
        stroke="red"
        strokeDasharray="5,5"
      />
      <circle
        cx={args.x2}
        cy={args.y2}
        r={args.offset}
        fill="none"
        stroke="red"
        strokeDasharray="5,5"
      />
      <CurvedArrow {...args} />
    </svg>
  ),
} as Meta;

type Story = StoryObj<typeof CurvedArrow>;

export const Default: Story = {};

export const Dashed: Story = {
  args: {
    dash: { length: 10, spacing: 2.5 },
  },
};

export const Upwards: Story = {
  args: {
    x1: 50,
    y1: 350,
    x2: 200,
    y2: 200,
    x3: 350,
    y3: 350,
  },
};

export const Failed: Story = {
  args: {
    onRenderCenter: (x, y, angle) => (
      <Cross
        x={x}
        y={y}
        width={5}
        length={20}
        angle={angle}
        fill="blue"
        stroke="red"
        strokeWidth={2}
      />
    ),
  },
};
