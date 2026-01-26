import type { Meta, StoryObj } from "@storybook/react";
import { CreateGame } from "./CreateGame";
import { getVariantsListMockHandler } from "@/api/generated/endpoints";
import { mockVariants } from "@/mocks";
import { withHomeLayout } from "@/stories/decorators";

const meta = {
  title: "Screens/Home/CreateGame",
  component: CreateGame,
  decorators: [withHomeLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/create-game",
      initialEntries: ["/create-game"],
    },
    msw: {
      handlers: [getVariantsListMockHandler(mockVariants)],
    },
  },
} satisfies Meta<typeof CreateGame>;

export default meta;
type Story = StoryObj<typeof meta>;

export const StandardGame: Story = {};

export const SandboxGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/create-game?sandbox=true"],
    },
  },
};
