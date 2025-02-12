import { Meta, StoryObj } from "@storybook/react";
import { Arrow } from "./arrow";
import { Cross } from "./cross";

export default {
  title: "Components/Shapes/Arrow",
  component: Arrow,
  args: {
    x1: 50,
    y1: 50,
    x2: 200,
    y2: 200,
    lineWidth: 5,
    fill: "blue",
    stroke: "red",
    strokeWidth: 1,
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
      <Arrow {...args} />
    </svg>
  ),
} as Meta;

type Story = StoryObj<typeof Arrow>;

export const Default: Story = {};

export const Dashed: Story = {
  args: {
    dash: { length: 10, spacing: 2.5 },
  },
};

export const Failed: Story = {
  args: {
    onRenderCenter: (x, y, angle) => {
      return (
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
      );
    },
  },
};
