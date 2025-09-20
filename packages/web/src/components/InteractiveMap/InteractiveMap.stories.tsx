import { Meta, StoryObj } from "@storybook/react";
import { InteractiveMap } from "./InteractiveMap";

const LONDON = {
  id: "lon",
  name: "London",
  type: "land",
  supplyCenter: true,
}

const ENGLAND = {
  name: "England",
  color: "rgb(255, 0, 0)",
}


export default {
  title: "Components/InteractiveMap",
  component: InteractiveMap,
  args: {
    interactive: true,
    phase: {
      units: [
        {
          type: "Army",
          nation: ENGLAND,
          province: LONDON,
        }
      ],
      supplyCenters: [
        {
          province: LONDON,
          nation: ENGLAND,
        }
      ]
    },
    variant: {
      id: "classical",
      nations: [
        ENGLAND,
      ]
    },
    orders: [
      {
        nation: "England",
        orders: [
          {
            id: 1,
            orderType: "Hold",
            source: {
              id: "lon",
              name: "London",
              type: "land",
              supplyCenter: true
            }
          }
        ]
      }
    ],
    selected: [],
    onClickProvince: () => { },
  },
} as Meta;

type Story = StoryObj<typeof InteractiveMap>;

export const Default: Story = {};
