import type { Meta, StoryObj } from "@storybook/react";
import { GameInfoScreen } from "./GameInfo";
import {
  getGameRetrieveMockHandler,
  getGamePhaseRetrieveMockHandler,
  getVariantsListMockHandler,
  GameRetrieve,
} from "@/api/generated/endpoints";
import { mockGames, mockVariants, mockPhaseMovement } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/GameInfoScreen",
  component: GameInfoScreen,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game-info/:gameId",
    },
  },
} satisfies Meta<typeof GameInfoScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActiveGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/game-info/game-1"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};

export const PendingGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/game-info/game-3"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[2] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};

export const PrivateGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/game-info/game-4"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[3] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};

export const CompletedGameSoloVictory: Story = {
  parameters: {
    router: {
      initialEntries: ["/game-info/game-5"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[4] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};

export const CompletedGameDraw: Story = {
  parameters: {
    router: {
      initialEntries: ["/game-info/game-6"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[5] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};
