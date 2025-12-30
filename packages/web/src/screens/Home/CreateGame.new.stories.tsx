import type { Meta, StoryObj } from "@storybook/react";
import { CreateGame } from "./CreateGame.new";
import { getVariantsListMockHandler } from "@/api/generated/endpoints";
import { mockVariants } from "@/mocks";
import { HomeLayout } from "../../components/HomeLayout";

const meta = {
  title: "Screens/CreateGame",
  component: CreateGame,
  render: args => (
    <HomeLayout>
      <CreateGame {...args} />
    </HomeLayout>
  ),
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
