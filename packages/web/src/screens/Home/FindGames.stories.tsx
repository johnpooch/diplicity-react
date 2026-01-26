import type { Meta, StoryObj } from "@storybook/react";
import { FindGames } from "./FindGames";
import {
  getGamePhaseRetrieveMockHandler,
  getGamesListMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockVariants, mockPendingGames, mockPhaseMovement } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/FindGames",
  component: FindGames,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/find-games",
      initialEntries: ["/find-games"],
    },
    msw: {
      handlers: [
        getGamesListMockHandler(mockPendingGames),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
} satisfies Meta<typeof FindGames>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const NoGames: Story = {
  parameters: {
    msw: {
      handlers: [
        getGamesListMockHandler([]),
        getVariantsListMockHandler(mockVariants),
      ],
    },
  },
};
