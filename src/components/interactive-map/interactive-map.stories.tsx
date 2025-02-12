import { Meta, StoryObj } from "@storybook/react";
import { InteractiveMap } from "./interactive-map";
import classical from "../../data/map/classical.json";

export default {
  title: "Components/InteractiveMap",
  component: InteractiveMap,
  args: {
    map: classical,
    units: {
      edi: {
        unitType: "fleet",
        nation: "England",
      },
      hol: {
        unitType: "army",
        nation: "England",
      },
      den: {
        unitType: "army",
        nation: "England",
      },
      bot: {
        unitType: "fleet",
        nation: "England",
      },
      spa: {
        unitType: "army",
        nation: "France",
      },
      gol: {
        unitType: "fleet",
        nation: "France",
      },
      wes: {
        unitType: "fleet",
        nation: "France",
      },
      tun: {
        unitType: "fleet",
        nation: "France",
      },
      tus: {
        unitType: "army",
        nation: "France",
      },
      gal: {
        unitType: "army",
        nation: "France",
      },
      boh: {
        unitType: "army",
        nation: "France",
      },
      sil: {
        unitType: "army",
        nation: "Germany",
      },
      mun: {
        unitType: "army",
        nation: "Germany",
      },
      bot: {
        unitType: "fleet",
        nation: "England",
      },
    },
    nationColors: {
      England: "rgb(33, 150, 243)",
      France: "rgb(128, 222, 234)",
      Germany: "rgb(144, 164, 174)",
      Italy: "rgb(76, 175, 80)",
      Austria: "rgb(244, 67, 54)",
      Russia: "rgb(245, 245, 245)",
      Turkey: "rbg(255, 193, 7)",
    },
    supplyCenters: {
      lon: "England",
      lvp: "England",
      edi: "England",
      nor: "England",
      swe: "England",
      stp: "Russia",
      mos: "Russia",
      spa: "France",
      bre: "France",
      par: "France",
      mar: "France",
      tun: "France",
      bel: "France",
      hol: "France",
      kie: "France",
      ber: "France",
      war: "Germany",
      mun: "Germany",
      ven: "Italy",
      nap: "Italy",
      gre: "Italy",
      rom: "Italy",
      vie: "Austria",
      bud: "Austria",
      tri: "Austria",
      ser: "Austria",
      rum: "Turkey",
      bul: "Turkey",
      con: "Turkey",
      smy: "Turkey",
      sev: "Turkey",
    },
    orders: {
      lvp: {
        type: "move",
        target: "wal",
        aux: "edi",
        outcome: "failed",
      },
      lon: {
        type: "support",
        target: "wal",
        aux: "lvp",
        outcome: "failed",
      },
      edi: {
        type: "hold",
        outcome: "failed",
      },
    },
  },
} as Meta;

type Story = StoryObj<typeof InteractiveMap>;

export const Default: Story = {};
