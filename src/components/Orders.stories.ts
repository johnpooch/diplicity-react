import type { Meta, StoryObj } from "@storybook/react";
import { Orders } from "./Orders";
import { withFullScreenContainerDecorator } from "../storybook";

const armySvg = `https://diplicity-engine.appspot.com/Variant/France%20vs%20Austria/Units/Army.svg`;
const fleetSvg = `https://diplicity-engine.appspot.com/Variant/France%20vs%20Austria/Units/Fleet.svg`;

const meta: Meta<typeof Orders> = {
  title: "Components/Orders",
  component: Orders,
  parameters: {
    layout: "fullscreen",
    viewport: {
      defaultViewport: "mobile1",
    },
  },
  decorators: [withFullScreenContainerDecorator]
};

export default meta;

type Story = StoryObj<typeof Orders>;

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const WithOneOrder: Story = {
  args: {
    isLoading: false,
    orders: [
      {
        nation: "France",
        orders: [
          {
            source: "Marseilles",
            orderType: "Move",
            unitTypeSvg: armySvg,
            target: "Burgundy",
            onClickDelete: () => { },
          },
        ],
      },
    ],
  },
};

export const WithMultipleOrders: Story = {
  args: {
    isLoading: false,
    orders: [
      {
        nation: "France",
        orders: [
          {
            source: "Marseilles",
            orderType: "move",
            unitTypeSvg: armySvg,
            target: "Burgundy",
            onClickDelete: () => { },
          },
          {
            source: "Burgundy",
            orderType: "hold",
            unitTypeSvg: armySvg,
            target: "Marseilles",
            onClickDelete: () => { },
          },
        ],
      },
      {
        nation: "Austria",
        orders: [
          {
            source: "Vienna",
            orderType: "move",
            unitTypeSvg: armySvg,
            target: "Galicia",
          },
          {
            source: "Galicia",
            orderType: "support",
            unitTypeSvg: fleetSvg,
            target: "Vienna",
            aux: "Trieste",
          },
        ],
      },
    ],
  },
};
