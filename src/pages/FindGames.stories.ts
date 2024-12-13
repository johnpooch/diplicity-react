import type { Meta, StoryObj } from "@storybook/react";
import FindGames from "./FindGames";

const meta = {
    title: "Pages/FindGames",
    component: FindGames,
    parameters: {
        layout: "centered",
    },
} satisfies Meta<typeof FindGames>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
