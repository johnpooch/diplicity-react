import type { Meta, StoryObj } from "@storybook/react";
import { MapScreen } from "./MapScreen";
import {
  getGameRetrieveMockHandler,
  getVariantsListMockHandler,
  getGamePhaseRetrieveMockHandler,
  getGamePhaseStatesListMockHandler,
  getGameOrdersListMockHandler,
  getGamePhasesListMockHandler,
  GameRetrieve,
  PhaseList,
} from "@/api/generated/endpoints";
import {
  mockGames,
  mockVariants,
  mockPhaseMovement,
  mockPhaseStates,
  mockOrders,
} from "@/mocks";
import { withGameDetailLayout } from "@/stories/decorators";

const mockPhasesList: PhaseList[] = [
  {
    id: 1,
    ordinal: 1,
    name: "Spring 1901 Movement",
    season: "Spring",
    year: 1901,
    type: "Movement",
    status: "active",
  },
];

const meta = {
  title: "Screens/GameDetail/MapScreen",
  component: MapScreen,
  decorators: [withGameDetailLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game/:gameId/phase/:phaseId",
    },
  },
} satisfies Meta<typeof MapScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhasesListMockHandler(mockPhasesList),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGamePhaseStatesListMockHandler(mockPhaseStates),
        getGameOrdersListMockHandler(mockOrders),
      ],
    },
  },
};
