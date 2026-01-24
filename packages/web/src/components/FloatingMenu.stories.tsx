import { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { FloatingMenu, FloatingMenuItem } from "./FloatingMenu";
import { Button } from "@/components/ui/button";

export default {
  title: "Components/FloatingMenu",
  component: FloatingMenu,
  parameters: {
    layout: "fullscreen",
  },
} as Meta;

type Story = StoryObj<typeof FloatingMenu>;

// Template for interactive stories
const InteractiveTemplate = (
  args: React.ComponentProps<typeof FloatingMenu>
) => {
  const [open, setOpen] = useState(false);
  const [anchorPoint, setAnchorPoint] = useState({ x: 200, y: 150 });

  const handleMapClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    setAnchorPoint({ x, y });
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleMenuItemClick = () => {
    setOpen(false);
  };

  return (
    <div className="relative h-screen w-screen bg-muted">
      {/* Simulated map area */}
      <div
        onClick={handleMapClick}
        className="flex h-full w-full cursor-pointer flex-col items-center justify-center gap-2"
      >
        <h4 className="text-2xl text-muted-foreground">
          Click anywhere to open menu
        </h4>
        <p className="text-muted-foreground">
          (Resize browser to test mobile behavior)
        </p>

        {/* Visual indicator of click position */}
        <div
          className="bg-primary absolute size-5 rounded-full transition-opacity"
          style={{
            left: anchorPoint.x - 10,
            top: anchorPoint.y - 10,
            opacity: open ? 1 : 0.3,
          }}
        />
      </div>

      <FloatingMenu
        {...args}
        open={open}
        x={anchorPoint.x}
        y={anchorPoint.y}
        onClose={handleClose}
      >
        <FloatingMenuItem onClick={handleMenuItemClick}>Hold</FloatingMenuItem>
        <FloatingMenuItem onClick={handleMenuItemClick}>Move</FloatingMenuItem>
        <FloatingMenuItem onClick={handleMenuItemClick}>
          Support
        </FloatingMenuItem>
        <FloatingMenuItem onClick={handleMenuItemClick}>
          Convoy
        </FloatingMenuItem>
      </FloatingMenu>
    </div>
  );
};

export const Interactive: Story = {
  render: InteractiveTemplate,
  args: {},
};

// Test positioning near edges
const EdgeTestTemplate = (args: React.ComponentProps<typeof FloatingMenu>) => {
  const [menus, setMenus] = useState<
    Array<{ x: number; y: number; id: number }>
  >([]);

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    setMenus([{ x, y, id: Date.now() }]);
  };

  const handleClose = () => {
    setMenus([]);
  };

  const corners = [
    { x: 50, y: 50, label: "Top-left" },
    { x: window.innerWidth - 50, y: 50, label: "Top-right" },
    { x: 50, y: window.innerHeight - 50, label: "Bottom-left" },
    {
      x: window.innerWidth - 50,
      y: window.innerHeight - 50,
      label: "Bottom-right",
    },
  ];

  return (
    <div className="relative h-screen w-screen bg-background">
      <div onClick={handleClick} className="relative h-full w-full">
        <h5 className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center text-xl">
          Click anywhere to test positioning
        </h5>

        {/* Corner markers */}
        {corners.map((corner, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            className="absolute min-w-20"
            style={{
              left: corner.x - 40,
              top: corner.y - 20,
            }}
            onClick={e => {
              e.stopPropagation();
              setMenus([{ x: corner.x, y: corner.y, id: Date.now() }]);
            }}
          >
            {corner.label}
          </Button>
        ))}
      </div>

      {menus.map(menu => (
        <FloatingMenu
          key={menu.id}
          {...args}
          open={true}
          x={menu.x}
          y={menu.y}
          onClose={handleClose}
        >
          <FloatingMenuItem onClick={handleClose}>Option 1</FloatingMenuItem>
          <FloatingMenuItem onClick={handleClose}>Option 2</FloatingMenuItem>
          <FloatingMenuItem onClick={handleClose}>Option 3</FloatingMenuItem>
        </FloatingMenu>
      ))}
    </div>
  );
};

export const EdgePositioning: Story = {
  render: EdgeTestTemplate,
  args: {},
};

// Test with container element
const ContainerTemplate = (args: React.ComponentProps<typeof FloatingMenu>) => {
  const [open, setOpen] = useState(false);
  const [anchorPoint, setAnchorPoint] = useState({ x: 100, y: 100 });
  const [container, setContainer] = useState<HTMLElement | null>(null);

  const handleContainerClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    setAnchorPoint({ x, y });
    setOpen(true);
  };

  return (
    <div className="h-screen w-screen bg-muted p-4">
      <h5 className="mb-2 text-xl">Container-relative positioning</h5>
      <div
        ref={setContainer}
        onClick={handleContainerClick}
        className="relative flex h-96 w-[600px] cursor-pointer items-center justify-center rounded border-2 border-primary bg-background"
      >
        <span>Click inside this container</span>

        <div
          className="bg-secondary absolute size-2.5 rounded-full"
          style={{
            left: anchorPoint.x - 5,
            top: anchorPoint.y - 5,
            opacity: open ? 1 : 0.3,
          }}
        />
      </div>
      <FloatingMenu
        {...args}
        open={open}
        x={anchorPoint.x}
        y={anchorPoint.y}
        container={container}
        onClose={() => setOpen(false)}
      >
        <FloatingMenuItem onClick={() => setOpen(false)}>
          Container Option 1
        </FloatingMenuItem>
        <FloatingMenuItem onClick={() => setOpen(false)}>
          Container Option 2
        </FloatingMenuItem>
      </FloatingMenu>
    </div>
  );
};

export const WithContainer: Story = {
  render: ContainerTemplate,
  args: {},
};

// Simple static example
export const Default: Story = {
  args: {
    open: true,
    x: 200,
    y: 150,
  },
  render: args => (
    <div className="h-screen w-screen bg-muted">
      <FloatingMenu {...args}>
        <FloatingMenuItem>Hold</FloatingMenuItem>
        <FloatingMenuItem>Move</FloatingMenuItem>
        <FloatingMenuItem>Support</FloatingMenuItem>
      </FloatingMenu>
    </div>
  ),
};
