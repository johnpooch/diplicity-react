import type { Meta, StoryObj } from "@storybook/react";
import { HomeLayout } from "./HomeLayout";
import { Navigation } from "./Navigation";
import { AppBar } from "./AppBar.new";
import { Button } from "@/components/ui/button";
import { Icon, IconName } from "./Icon";
import { navigationItems } from "../navigation/navigationItems";

/**
 * HomeLayout is a responsive app shell that provides a flexible three-column
 * layout with optional bottom navigation. It handles all responsive behavior
 * declaratively through the breakpoints prop.
 */
const meta = {
  title: "Layout/HomeLayout",
  component: HomeLayout,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof HomeLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

// Helper to create navigation items with active state
const createNavItems = (activePath: string = "/") =>
  navigationItems.map(item => ({
    ...item,
    isActive: item.path === activePath,
  }));

const MockContent = () => (
  <div className="space-y-4 p-6">
    <h1 className="text-2xl font-bold">Main Content Area</h1>
    <div className="space-y-2">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="rounded-lg border p-4">
          <div className="h-4 w-3/4 rounded bg-muted" />
          <div className="mt-2 h-3 w-1/2 rounded bg-muted" />
        </div>
      ))}
    </div>
  </div>
);

const MockInfoPanel = () => (
  <div className="space-y-4 p-6">
    <h2 className="font-semibold">Info Panel</h2>
    <p className="text-sm text-muted-foreground">
      Welcome message and helpful links would go here.
    </p>
  </div>
);

export const Default: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <>
        <AppBar
          title="Game Details"
          leftAction={
            <Button
              variant="ghost"
              size="icon"
              onClick={() => console.log("Back clicked")}
              aria-label="Go back"
            >
              <Icon name={IconName.Back} variant="lucide" size={20} />
            </Button>
          }
          rightAction={
            <Button
              variant="ghost"
              size="icon"
              onClick={() => console.log("Menu clicked")}
              aria-label="Open menu"
            >
              <Icon name={IconName.Menu} variant="lucide" size={20} />
            </Button>
          }
        />
        <MockContent />
      </>
    ),
    right: <MockInfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};
