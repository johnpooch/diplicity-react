import type { Meta, StoryObj } from "@storybook/react";
import { GameInfo } from "./GameInfo.new";
import {
  getGameRetrieveMockHandler,
  getGamePhaseRetrieveMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockGames, mockVariants, mockPhaseMovement } from "@/mocks";
import { HomeLayout } from "../../components/HomeLayout";

const meta = {
  title: "Screens/GameInfo",
  component: GameInfo,
  render: args => (
    <HomeLayout>
      <GameInfo {...args} />
    </HomeLayout>
  ),
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game-info/:gameId",
    },
  },
} satisfies Meta<typeof GameInfo>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActiveGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/game-info/game-1"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0]),
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
        getGameRetrieveMockHandler(mockGames[2]),
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
        getGameRetrieveMockHandler(mockGames[3]),
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
        getGameRetrieveMockHandler(mockGames[4]),
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
        getGameRetrieveMockHandler(mockGames[5]),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};
