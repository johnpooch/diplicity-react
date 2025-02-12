import { Meta, StoryObj } from "@storybook/react";
import { InteractiveMap } from "./interactive-map";
import classical from "../../data/map/classical.json";

export default {
  title: "Components/InteractiveMap",
  component: InteractiveMap,
  args: {
    map: classical,
    units: {
      lon: {
        unitType: "army",
        nation: "England",
      },
      lvp: {
        unitType: "fleet",
        nation: "England",
      },
      edi: {
        unitType: "army",
        nation: "England",
      },
    },
    nationColors: {
      England: "rgb(255, 0, 0)",
      France: "rgb(0, 0, 255)",
      Germany: "rgb(0, 255, 0)",
      Italy: "rgb(255, 255, 0)",
      Austria: "rgb(255, 0, 255)",
      Russia: "rgb(0, 255, 255)",
    },
    supplyCenters: {
      lon: "England",
      lvp: "England",
      edi: "England",
    },
    orders: {
      lvp: {
        type: "move",
        target: "wal",
        aux: "edi",
        outcome: "succeeded",
      },
      lon: {
        type: "support",
        target: "wal",
        aux: "lvp",
        outcome: "succeeded",
      },
    },
  },
} as Meta;

type Story = StoryObj<typeof InteractiveMap>;

export const Default: Story = {};
