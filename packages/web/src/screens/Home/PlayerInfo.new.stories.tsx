import type { Meta, StoryObj } from "@storybook/react";
import { PlayerInfo } from "./PlayerInfo.new";
import {
  getGameRetrieveMockHandler,
  getGamePhaseRetrieveMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockGames, mockVariants, mockPhaseMovement } from "@/mocks";
import { HomeLayout } from "../../components/HomeLayout";

const meta = {
  title: "Screens/PlayerInfo",
  component: PlayerInfo,
  render: args => (
    <HomeLayout>
      <PlayerInfo {...args} />
    </HomeLayout>
  ),
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/player-info/:gameId",
      initialEntries: ["/player-info/game-1"],
    },
  },
} satisfies Meta<typeof PlayerInfo>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActiveGame: Story = {
  parameters: {
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
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[2]),
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
        getGameRetrieveMockHandler(mockGames[4]),
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
        getGameRetrieveMockHandler(mockGames[5]),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
};
