import type { Meta, StoryObj } from "@storybook/react";
import { AppBar } from "./AppBar.new";
import { Button } from "@/components/ui/button";
import { Icon, IconName } from "./Icon";

const meta = {
  title: "Components/AppBar",
  component: AppBar,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof AppBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "Game Details",
    leftAction: (
      <Button
        variant="ghost"
        size="icon"
        onClick={() => console.log("Back clicked")}
        aria-label="Go back"
      >
        <Icon name={IconName.Back} variant="lucide" size={20} />
      </Button>
    ),
    rightAction: (
      <Button
        variant="ghost"
        size="icon"
        onClick={() => console.log("Menu clicked")}
        aria-label="Open menu"
      >
        <Icon name={IconName.Menu} variant="lucide" size={20} />
      </Button>
    ),
  },
};

export const WithoutLeftAction: Story = {
  args: {
    title: "Home",
    rightAction: (
      <Button
        variant="ghost"
        size="icon"
        onClick={() => console.log("Menu clicked")}
        aria-label="Open menu"
      >
        <Icon name={IconName.Menu} variant="lucide" size={20} />
      </Button>
    ),
  },
};

export const WithoutRightAction: Story = {
  args: {
    title: "Detail Page",
    leftAction: (
      <Button
        variant="ghost"
        size="icon"
        onClick={() => console.log("Back clicked")}
        aria-label="Go back"
      >
        <Icon name={IconName.Back} variant="lucide" size={20} />
      </Button>
    ),
  },
};

export const MinimalWithTitle: Story = {
  args: {
    title: "Simple Title",
  },
};

export const CustomActions: Story = {
  args: {
    title: "Custom Actions",
    leftAction: (
      <Button
        variant="ghost"
        size="icon"
        onClick={() => console.log("Close clicked")}
        aria-label="Close"
      >
        <Icon name={IconName.Close} variant="lucide" size={20} />
      </Button>
    ),
    rightAction: (
      <div className="flex gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => console.log("Edit clicked")}
          aria-label="Edit"
        >
          <Icon name={IconName.Edit} variant="lucide" size={20} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => console.log("Delete clicked")}
          aria-label="Delete"
        >
          <Icon name={IconName.Delete} variant="lucide" size={20} />
        </Button>
      </div>
    ),
  },
};
