import { Meta, StoryObj } from "@storybook/react";
import { InteractiveMap } from "./InteractiveMap";

const Nations = {
  England: {
    name: "England",
    color: "#2196F3",
  },
  France: {
    name: "France",
    color: "#80DEEA",
  },
  Germany: {
    name: "Germany",
    color: "#90A4AE",
  },
  Italy: {
    name: "Italy",
    color: "#4CAF50",
  },
  Austria: {
    name: "Austria",
    color: "#F44336",
  },
  Turkey: {
    name: "Turkey",
    color: "#FFC107",
  },
  Russia: {
    name: "Russia",
    color: "#F5F5F5",
  }
}

const Provinces = {
  London: {
    id: "lon",
    name: "London",
    type: "coastal",
    supplyCenter: true,
  },
  AdriaticSea: {
    id: "adr",
    name: "Adriatic Sea",
    type: "sea",
    supplyCenter: false,
  },
  Trieste: {
    id: "tri",
    name: "Trieste",
    type: "coastal",
    supplyCenter: true,
  },
  Apulia: {
    id: "apu",
    name: "Apulia",
    type: "coastal",
    supplyCenter: false,
  },
  Berlin: {
    id: "ber",
    name: "Berlin",
    type: "coastal",
    supplyCenter: true,
  },
  Kiel: {
    id: "kie",
    name: "Kiel",
    type: "coastal",
    supplyCenter: true,
  },
  Munich: {
    id: "mun",
    name: "Munich",
    type: "land",
    supplyCenter: true,
  },
  Bohemia: {
    id: "boh",
    name: "Bohemia",
    type: "land",
    supplyCenter: false,
  },
  Tyrolia: {
    id: "tyr",
    name: "Tyrolia",
    type: "land",
    supplyCenter: false,
  },
  Venice: {
    id: "ven",
    name: "Venice",
    type: "coastal",
    supplyCenter: true,
  },
  Rome: {
    id: "rom",
    name: "Rome",
    type: "coastal",
    supplyCenter: true,
  },
  Tuscany: {
    id: "tus",
    name: "Tuscany",
    type: "coastal",
    supplyCenter: false,
  },
  Holland: {
    id: "hol",
    name: "Holland",
    type: "coastal",
    supplyCenter: true,
  },
  Paris: {
    id: "par",
    name: "Paris",
    type: "land",
    supplyCenter: true,
  },
  Burgundy: {
    id: "bur",
    name: "Burgundy",
    type: "land",
    supplyCenter: false,
  },
  Marseilles: {
    id: "mar",
    name: "Marseilles",
    type: "coastal",
    supplyCenter: true,
  },
  Piedmont: {
    id: "pie",
    name: "Piedmont",
    type: "coastal",
    supplyCenter: false,
  },
  Vienna: {
    id: "vie",
    name: "Vienna",
    type: "land",
    supplyCenter: true,
  },
  Budapest: {
    id: "bud",
    name: "Budapest",
    type: "land",
    supplyCenter: true,
  },
  Serbia: {
    id: "ser",
    name: "Serbia",
    type: "land",
    supplyCenter: true,
  },
  Ankara: {
    id: "ank",
    name: "Ankara",
    type: "coastal",
    supplyCenter: true,
  },
  Constantinople: {
    id: "con",
    name: "Constantinople",
    type: "coastal",
    supplyCenter: true,
  },
  BlackSea: {
    id: "bla",
    name: "Black Sea",
    type: "sea",
    supplyCenter: false,
  },
  EnglishChannel: {
    id: "eng",
    name: "English Channel",
    type: "sea",
    supplyCenter: false,
  },
  NorthSea: {
    id: "nth",
    name: "North Sea",
    type: "sea",
    supplyCenter: false,
  },
  Wales: {
    id: "wal",
    name: "Wales",
    type: "coastal",
    supplyCenter: false,
  },
  Brest: {
    id: "bre",
    name: "Brest",
    type: "coastal",
    supplyCenter: true,
  },
  Picardy: {
    id: "pic",
    name: "Picardy",
    type: "coastal",
    supplyCenter: false,
  },
  MidAtlantic: {
    id: "mid",
    name: "Mid Atlantic",
    type: "sea",
    supplyCenter: false,
  },
  Portugal: {
    id: "por",
    name: "Portugal",
    type: "coastal",
    supplyCenter: true,
  },
  Moscow: {
    id: "mos",
    name: "Moscow",
    type: "land",
    supplyCenter: true,
  },
  StPetersburg: {
    id: "stp",
    name: "St Petersburg",
    type: "coastal",
    supplyCenter: true,
  },
  Bulgaria: {
    id: "bul",
    name: "Bulgaria",
    type: "land",
    supplyCenter: false,
  },
}


export default {
  title: "Components/InteractiveMap",
  component: InteractiveMap,
  args: {
    interactive: true,
    phase: {
      units: [
        // England
        {
          type: "Army",
          nation: Nations.England,
          province: Provinces.London,
        },
        {
          type: "Fleet",
          nation: Nations.England,
          province: Provinces.MidAtlantic,
        },
        // France
        {
          type: "Army",
          nation: Nations.France,
          province: Provinces.Paris,
        },
        {
          type: "Army",
          nation: Nations.France,
          province: Provinces.Burgundy,
        },
        {
          type: "Army",
          nation: Nations.France,
          province: Provinces.Brest,
        },
        {
          type: "Army",
          nation: Nations.France,
          province: Provinces.Marseilles,
        },
        // Germany
        {
          type: "Army",
          nation: Nations.Germany,
          province: Provinces.Kiel,
        },
        {
          type: "Army",
          nation: Nations.Germany,
          province: Provinces.Berlin,
        },
        {
          type: "Army",
          nation: Nations.Germany,
          province: Provinces.Munich,
        },
        // Italy
        {
          type: "Fleet",
          nation: Nations.Italy,
          province: Provinces.AdriaticSea,
        },
        {
          type: "Army",
          nation: Nations.Italy,
          province: Provinces.Apulia,
        },
        {
          type: "Army",
          nation: Nations.Italy,
          province: Provinces.Rome,
        },
        {
          type: "Fleet",
          nation: Nations.Italy,
          province: Provinces.Venice,
          dislodgedBy: {
            type: "Army",
            nation: Nations.Germany,
          }
        },
        // Austria
        {
          type: "Army",
          nation: Nations.Austria,
          province: Provinces.Vienna,
        },
        {
          type: "Army",
          nation: Nations.Austria,
          province: Provinces.Budapest,
        },
        // Turkey
        {
          type: "Army",
          nation: Nations.Turkey,
          province: Provinces.Ankara,
        },
        {
          type: "Fleet",
          nation: Nations.Turkey,
          province: Provinces.Constantinople,
        },
        {
          type: "Fleet",
          nation: Nations.Turkey,
          province: Provinces.Bulgaria,
        }
      ],
      supplyCenters: [
        {
          province: Provinces.London,
          nation: Nations.England,
        },
        {
          province: Provinces.Paris,
          nation: Nations.France,
        }
      ]
    },
    variant: {
      id: "classical",
      nations: [
        Nations.England,
        Nations.France,
        Nations.Germany,
        Nations.Italy,
        Nations.Austria,
        Nations.Turkey,
        Nations.Russia,
      ]
    },
    orders: [
      // Hold order - Successful
      {
        id: 1,
        nation: Nations.England,
        orderType: "Hold",
        source: Provinces.London,
        resolution: { status: "Succeeded" }
      },
      // Hold order - Failed
      {
        id: 2,
        nation: Nations.Turkey,
        orderType: "Hold",
        source: Provinces.Ankara,
        resolution: { status: "Failed" }
      },
      // Move order - Successful
      {
        id: 3,
        nation: Nations.Germany,
        orderType: "Move",
        source: Provinces.Kiel,
        target: Provinces.Holland,
      },
      // Support Hold - Successful
      {
        id: 4,
        nation: Nations.Germany,
        orderType: "Support",
        source: Provinces.Munich,
        target: Provinces.Berlin,
        aux: Provinces.Berlin,
        resolution: { status: "Succeeded" }
      },
      {
        id: 41,
        nation: Nations.Germany,
        orderType: "Hold",
        source: Provinces.Berlin,
      },
      // Support Move - Successful
      {
        id: 5,
        nation: Nations.Austria,
        orderType: "Support",
        source: Provinces.Vienna,
        target: Provinces.Trieste,
        aux: Provinces.Budapest,
        resolution: { status: "Succeeded" }
      },
      {
        id: 6,
        nation: Nations.Austria,
        orderType: "Move",
        source: Provinces.Budapest,
        target: Provinces.Trieste,
        resolution: { status: "Failed" }
      },
      // Convoy - Successful
      {
        id: 7,
        nation: Nations.Italy,
        orderType: "Convoy",
        source: Provinces.AdriaticSea,
        target: Provinces.Trieste,
        aux: Provinces.Apulia,
        resolution: { status: "Succeeded" }
      },
      // Convoy - Failed
      {
        id: 8,
        nation: Nations.England,
        orderType: "Convoy",
        source: Provinces.MidAtlantic,
        target: Provinces.Portugal,
        aux: Provinces.Brest,
        resolution: { status: "Failed" }
      },
      {
        id: 81,
        nation: Nations.France,
        orderType: "Move",
        source: Provinces.Brest,
        target: Provinces.Portugal,
        resolution: { status: "Failed" }
      },
      // Move via Convoy (shown as Move)
      {
        id: 9,
        nation: Nations.Italy,
        orderType: "MoveViaConvoy",
        source: Provinces.Apulia,
        target: Provinces.Trieste,
      },
      // Build orders
      {
        id: 10,
        nation: Nations.Russia,
        orderType: "Build",
        source: Provinces.Moscow,
        unitType: "Army",
      },
      {
        id: 11,
        nation: Nations.Russia,
        orderType: "Build",
        source: Provinces.StPetersburg,
        unitType: "Fleet",
      },
      // Additional movement orders for variety
      {
        id: 12,
        nation: Nations.France,
        orderType: "Move",
        source: Provinces.Paris,
        target: Provinces.Burgundy,
      },
      {
        id: 13,
        nation: Nations.Italy,
        orderType: "Move",
        source: Provinces.Rome,
        target: Provinces.Tuscany,
      },
      {
        id: 14,
        nation: Nations.Turkey,
        orderType: "Move",
        source: Provinces.Constantinople,
        target: Provinces.BlackSea,
        resolution: { status: "Failed" }
      },
      {
        id: 15,
        nation: Nations.Turkey,
        orderType: "Support",
        source: Provinces.Bulgaria,
        target: Provinces.BlackSea,
        aux: Provinces.Constantinople,
        resolution: { status: "Failed" }
      },
    ],
    selected: [],
    onClickProvince: () => { },
  },
} as Meta;

type Story = StoryObj<typeof InteractiveMap>;

export const Default: Story = {};
