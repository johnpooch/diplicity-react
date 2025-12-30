import type { Meta, StoryObj } from "@storybook/react";
import { FindGames } from "./FindGames.new";
import {
  getGamePhaseRetrieveMockHandler,
  getGamesListMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockVariants, mockPendingGames, mockPhaseMovement } from "@/mocks";
import { HomeLayout } from "../../components/HomeLayout";

const meta = {
  title: "Screens/FindGames",
  component: FindGames,
  render: args => (
    <HomeLayout>
      <FindGames {...args} />
    </HomeLayout>
  ),
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
