import type { Meta, StoryObj } from "@storybook/react";
import CreateGame from "./CreateGame";

const meta = {
  title: "Pages/CreateGame",
  component: CreateGame,
  parameters: {
    layout: "centered",
  },
} satisfies Meta<typeof CreateGame>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
