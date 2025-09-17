import React from "react";
import { Paper, MenuList, Portal, useMediaQuery, useTheme, Drawer, ClickAwayListener } from "@mui/material";
import { createUseStyles } from "./utils/styles";

export interface FloatingMenuProps {
  open: boolean;
  x: number;
  y: number;
  container?: Element | null;
  children: React.ReactNode;
  onClose?: () => void;
  PaperProps?: React.ComponentProps<typeof Paper>;
  DrawerProps?: React.ComponentProps<typeof Drawer>;
}

const useStyles = createUseStyles<FloatingMenuProps>(() => ({
  paper: {
    position: "fixed",
    zIndex: 1300,
    minWidth: 200,
    maxWidth: 300,
  },
  drawer: {
    "& .MuiDrawer-paper": {
      borderTopLeftRadius: (theme) => theme.shape.borderRadius * 2,
      borderTopRightRadius: (theme) => theme.shape.borderRadius * 2,
    },
  },
  menuList: {
    py: 1,
  },
}));

const FloatingMenu: React.FC<FloatingMenuProps> = (props) => {
  const theme = useTheme();
  const styles = useStyles(props);
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const getPosition = () => {
    const menuWidth = 200; // Approximate width
    const menuHeight = 200; // Approximate height

    let left: number;
    let top: number;

    if (props.container) {
      // Position relative to container
      const rect = props.container.getBoundingClientRect();
      left = rect.left + props.x;
      top = rect.top + props.y;
    } else {
      left = props.x;
      top = props.y;
    }

    // Adjust for screen edges
    if (left + menuWidth > window.innerWidth) {
      left = left - menuWidth;
    }

    if (top + menuHeight > window.innerHeight) {
      top = top - menuHeight;
    }

    // Ensure we don't go off the left or top edges
    left = Math.max(8, left);
    top = Math.max(8, top);

    return { top, left };

  };

  if (!props.open) return null;

  // Mobile: Bottom drawer
  if (isMobile) {
    return (
      <Drawer
        anchor="bottom"
        open={props.open}
        onClose={props.onClose}
        sx={styles.drawer}
        {...props.DrawerProps}
      >
        <MenuList sx={styles.menuList}>
          {props.children}
        </MenuList>
      </Drawer>
    );
  }

  // Desktop: Floating positioned menu
  const position = getPosition();

  return (
    <Portal>
      <ClickAwayListener onClickAway={props.onClose || (() => { })}>
        <Paper
          sx={{
            ...styles.paper,
            top: position.top,
            left: position.left,
          }}
          {...props.PaperProps}
        >
          <MenuList sx={styles.menuList}>
            {props.children}
          </MenuList>
        </Paper>
      </ClickAwayListener>
    </Portal>
  );
};

export { FloatingMenu };