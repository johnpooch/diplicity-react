import type { Meta, StoryObj } from "@storybook/react";
import { http, HttpResponse, delay } from "msw";
import { MyGames } from "./MyGames";
import {
  getGamePhaseRetrieveMockHandler,
  getGamesListMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockVariants, mockPendingGames, mockPhaseMovement } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/MyGames",
  component: MyGames,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      initialEntries: ["/"],
    },
    msw: {
      handlers: [
        getGamesListMockHandler(mockPendingGames),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
} satisfies Meta<typeof MyGames>;

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

export const Error: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get("*/games/", async () => {
          await delay(100);
          return new HttpResponse(
            JSON.stringify({ detail: "Internal server error" }),
            { status: 500 }
          );
        }),
        getVariantsListMockHandler(mockVariants),
      ],
    },
  },
};
