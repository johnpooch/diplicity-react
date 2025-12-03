import { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Button, MenuItem, Box, Typography } from "@mui/material";
import { FloatingMenu } from "./FloatingMenu";

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
    <Box
      sx={{
        height: "100vh",
        width: "100vw",
        position: "relative",
        bgcolor: "grey.100",
      }}
    >
      {/* Simulated map area */}
      <Box
        onClick={handleMapClick}
        sx={{
          width: "100%",
          height: "100%",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 2,
        }}
      >
        <Typography variant="h4" color="textSecondary">
          Click anywhere to open menu
        </Typography>
        <Typography variant="body1" color="textSecondary">
          (Resize browser to test mobile behavior)
        </Typography>

        {/* Visual indicator of click position */}
        <Box
          sx={{
            position: "absolute",
            left: anchorPoint.x - 10,
            top: anchorPoint.y - 10,
            width: 20,
            height: 20,
            borderRadius: "50%",
            bgcolor: "primary.main",
            opacity: open ? 1 : 0.3,
            transition: "opacity 0.2s",
          }}
        />
      </Box>

      <FloatingMenu onClose={handleClose} {...args}>
        <MenuItem onClick={handleMenuItemClick}>
          <Typography>Hold</Typography>
        </MenuItem>
        <MenuItem onClick={handleMenuItemClick}>
          <Typography>Move</Typography>
        </MenuItem>
        <MenuItem onClick={handleMenuItemClick}>
          <Typography>Support</Typography>
        </MenuItem>
        <MenuItem onClick={handleMenuItemClick}>
          <Typography>Convoy</Typography>
        </MenuItem>
      </FloatingMenu>
    </Box>
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
    <Box
      sx={{
        height: "100vh",
        width: "100vw",
        position: "relative",
        bgcolor: "grey.50",
      }}
    >
      <Box
        onClick={handleClick}
        sx={{
          width: "100%",
          height: "100%",
          position: "relative",
        }}
      >
        <Typography
          variant="h5"
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
          }}
        >
          Click anywhere to test positioning
        </Typography>

        {/* Corner markers */}
        {corners.map((corner, index) => (
          <Button
            key={index}
            variant="outlined"
            size="small"
            sx={{
              position: "absolute",
              left: corner.x - 40,
              top: corner.y - 20,
              minWidth: 80,
            }}
            onClick={e => {
              e.stopPropagation();
              setMenus([{ x: corner.x, y: corner.y, id: Date.now() }]);
            }}
          >
            {corner.label}
          </Button>
        ))}
      </Box>

      {menus.map(menu => (
        <FloatingMenu key={menu.id} onClose={handleClose} {...args}>
          <MenuItem onClick={handleClose}>
            <Typography>Option 1</Typography>
          </MenuItem>
          <MenuItem onClick={handleClose}>
            <Typography>Option 2</Typography>
          </MenuItem>
          <MenuItem onClick={handleClose}>
            <Typography>Option 3</Typography>
          </MenuItem>
        </FloatingMenu>
      ))}
    </Box>
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
    <Box sx={{ height: "100vh", width: "100vw", p: 4, bgcolor: "grey.50" }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Container-relative positioning
      </Typography>
      <Box
        ref={el => {
          setContainer(el as HTMLElement);
        }}
        onClick={handleContainerClick}
        sx={{
          width: 600,
          height: 400,
          bgcolor: "white",
          border: 2,
          borderColor: "primary.main",
          borderRadius: 1,
          position: "relative",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography>Click inside this container</Typography>

        <Box
          sx={{
            position: "absolute",
            left: anchorPoint.x - 5,
            top: anchorPoint.y - 5,
            width: 10,
            height: 10,
            borderRadius: "50%",
            bgcolor: "secondary.main",
            opacity: open ? 1 : 0.3,
          }}
        />
      </Box>
      <FloatingMenu
        container={container}
        onClose={() => setOpen(false)}
        {...args}
      >
        <MenuItem onClick={() => setOpen(false)}>
          <Typography>Container Option 1</Typography>
        </MenuItem>
        <MenuItem onClick={() => setOpen(false)}>
          <Typography>Container Option 2</Typography>
        </MenuItem>
      </FloatingMenu>
    </Box>
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
    children: (
      <>
        <MenuItem>
          <Typography>Hold</Typography>
        </MenuItem>
        <MenuItem>
          <Typography>Move</Typography>
        </MenuItem>
        <MenuItem>
          <Typography>Support</Typography>
        </MenuItem>
      </>
    ),
  },
  render: args => (
    <Box sx={{ height: "100vh", width: "100vw", bgcolor: "grey.100" }}>
      <FloatingMenu {...args} />
    </Box>
  ),
};
