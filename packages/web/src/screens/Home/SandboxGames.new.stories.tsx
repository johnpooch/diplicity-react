import type { Meta, StoryObj } from "@storybook/react";
import { SandboxGames } from "./SandboxGames.new";
import {
  getGamePhaseRetrieveMockHandler,
  getGamesListMockHandler,
  getVariantsListMockHandler,
} from "@/api/generated/endpoints";
import { mockVariants, mockSandboxGames, mockPhaseMovement } from "@/mocks";
import { HomeLayout } from "../../components/HomeLayout";

const meta = {
  title: "Screens/SandboxGames",
  component: SandboxGames,
  render: args => (
    <HomeLayout>
      <SandboxGames {...args} />
    </HomeLayout>
  ),
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
