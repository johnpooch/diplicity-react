import type { Meta, StoryObj } from "@storybook/react";
import { SandboxGames } from "./SandboxGames";
import {
  getGamePhaseRetrieveMockHandler,
  getGamesListMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockVariants, mockSandboxGames, mockPhaseMovement } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/SandboxGames",
  component: SandboxGames,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/sandbox",
      initialEntries: ["/sandbox"],
    },
    msw: {
      handlers: [
        getGamesListMockHandler(mockSandboxGames),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
      ],
    },
  },
} satisfies Meta<typeof SandboxGames>;

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
