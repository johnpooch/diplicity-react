import type { Meta, StoryObj } from "@storybook/react";
import { PlayerInfoScreen } from "./PlayerInfo";
import {
  getGameRetrieveMockHandler,
  getGamePhaseRetrieveMockHandler,
  getVariantsListMockHandler,
  GameRetrieve,
} from "@/api/generated/endpoints";
import { mockGames, mockVariants, mockPhaseMovement } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/PlayerInfoScreen",
  component: PlayerInfoScreen,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/player-info/:gameId",
      initialEntries: ["/player-info/game-1"],
    },
  },
} satisfies Meta<typeof PlayerInfoScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActiveGame: Story = {
  parameters: {
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
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[2] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};

export const CompletedGameSoloVictory: Story = {
  parameters: {
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
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[5] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};
