import type { Meta, StoryObj } from "@storybook/react";
import { Navigation } from "./Navigation";
import { IconName } from "./Icon";

const meta = {
  title: "Components/Navigation",
  component: Navigation,
  parameters: {
    layout: "padded",
  },
  argTypes: {
    variant: {
      control: "select",
      options: ["sidebar", "compact", "bottom"],
      description: "Visual variant of the navigation",
    },
    onItemClick: { action: "clicked" },
  },
} satisfies Meta<typeof Navigation>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockItems = [
  {
    label: "My Games",
    icon: IconName.MyGames,
    path: "/",
    isActive: false,
  },
  {
    label: "Find Games",
    icon: IconName.FindGames,
    path: "/find-games",
    isActive: false,
  },
  {
    label: "Create Game",
    icon: IconName.CreateGame,
    path: "/create-game",
    isActive: false,
  },
  {
    label: "Sandbox",
    icon: IconName.Sandbox,
    path: "/sandbox",
    isActive: false,
  },
  {
    label: "Profile",
    icon: IconName.Profile,
    path: "/profile",
    isActive: false,
  },
];

export const Sidebar: Story = {
  args: {
    items: mockItems.map((item, index) => ({
      ...item,
      isActive: index === 0,
    })),
    variant: "sidebar",
  },
};

export const Compact: Story = {
  args: {
    items: mockItems.map((item, index) => ({
      ...item,
      isActive: index === 0,
    })),
    variant: "compact",
  },
};

export const Bottom: Story = {
  args: {
    items: mockItems.map((item, index) => ({
      ...item,
      isActive: index === 0,
    })),
    variant: "bottom",
  },
};
