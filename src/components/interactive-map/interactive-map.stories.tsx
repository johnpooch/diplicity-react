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
      sil: {
        unitType: "army",
        nation: "Germany",
      },
      mun: {
        unitType: "army",
        nation: "Germany",
      },
      pie: {
        unitType: "fleet",
        nation: "Turkey",
      },
      ven: {
        unitType: "army",
        nation: "Italy",
      },
      rom: {
        unitType: "army",
        nation: "Italy",
      },
      nap: {
        unitType: "fleet",
        nation: "Italy",
      },
      apu: {
        unitType: "army",
        nation: "Austria",
      },
      adr: {
        unitType: "fleet",
        nation: "Italy",
      },
      tys: {
        unitType: "fleet",
        nation: "Turkey",
      },
      bur: {
        unitType: "army",
        nation: "France",
      },
      ion: {
        unitType: "fleet",
        nation: "Turkey",
      },
      ank: {
        unitType: "army",
        nation: "Turkey",
      },
      bud: {
        unitType: "army",
        nation: "Austria",
      },
      vie: {
        unitType: "army",
        nation: "Austria",
      },
      tyr: {
        unitType: "army",
        nation: "Austria",
      },
      boh: {
        unitType: "army",
        nation: "France",
      },
      sev: {
        unitType: "army",
        nation: "Turkey",
      },
      ukr: {
        unitType: "army",
        nation: "Russia",
      },
      mos: {
        unitType: "army",
        nation: "France",
      },
      war: {
        unitType: "army",
        nation: "Russia",
      },
      pru: {
        unitType: "army",
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
      Turkey: "rgb(255, 193, 7)",
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
      bur: "France",
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
      den: {
        type: "move",
        target: "swe",
        outcome: "success",
      },
      hol: {
        type: "move",
        target: "kie",
        outcome: "success",
      },
      bur: {
        type: "move",
        target: "mar",
        outcome: "success",
      },
      pie: {
        type: "move",
        target: "gol",
        outcome: "success",
      },
      wes: {
        type: "support",
        target: "tun",
        aux: "tun",
        outcome: "success",
      },
      gol: {
        type: "support",
        target: "pie",
        aux: "tus",
        outcome: "success",
      },
      tus: {
        type: "move",
        target: "pie",
        outcome: "failed",
      },
      rom: {
        type: "move",
        target: "tus",
        outcome: "success",
      },
      ven: {
        type: "support",
        target: "tus",
        aux: "rom",
        outcome: "success",
      },
      tun: {
        type: "hold",
        outcome: "success",
      },
      tys: {
        type: "move",
        target: "tun",
        outcome: "failed",
      },
      ion: {
        type: "support",
        target: "tun",
        aux: "tys",
        outcome: "success",
      },
      nap: {
        type: "move",
        target: "tys",
        outcome: "failed",
      },
      apu: {
        type: "move",
        target: "tri",
        outcome: "success",
      },
      spa: {
        type: "hold",
        outcome: "success",
      },
      ank: {
        type: "hold",
        outcome: "success",
      },
      mun: {
        type: "move",
        target: "tyr",
        outcome: "success",
      },
      boh: {
        type: "support",
        target: "tyr",
        aux: "mun",
        outcome: "failed",
      },
      vie: {
        type: "support",
        target: "boh",
        aux: "tyr",
        outcome: "success",
      },
      tyr: {
        type: "move",
        target: "boh",
        outcome: "success",
      },
      pru: {
        type: "move",
        target: "war",
        outcome: "failed",
      },
      sil: {
        type: "move",
        target: "war",
        outcome: "failed",
      },
      war: {
        type: "move",
        target: "gal",
        outcome: "failed",
      },
      gal: {
        type: "move",
        target: "rum",
        outcome: "success",
      },
      bud: {
        type: "move",
        target: "gal",
        outcome: "failed",
      },
      ukr: {
        type: "support",
        target: "mos",
        aux: "sev",
        outcome: "success",
      },
      sev: {
        type: "move",
        target: "mos",
        outcome: "success",
      },
      mos: {
        type: "hold",
        outcome: "failed",
      },
    },
  },
} as Meta;

type Story = StoryObj<typeof InteractiveMap>;

export const Default: Story = {};
