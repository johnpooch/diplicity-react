import React from "react";
import {
  Drawer,
  List,
  ListItem,
  useTheme,
} from "@mui/material";
import { IconName } from "./elements/Icon";
import { ListItemButton } from "./elements/Button";

const DrawerNavigationContext = React.createContext<
  | {
    value: string;
    onChange: (newValue: string) => void;
    variant: "expanded" | "collapsed";
  }
  | undefined
>(undefined);

type DrawerNavigationProps = React.PropsWithChildren<{
  value: string;
  onChange: (newValue: string) => void;
  variant: "expanded" | "collapsed";
}>;

const DrawerNavigation: React.FC<DrawerNavigationProps> = (props) => {
  const drawerWidth = props.variant === "expanded" ? 240 : 56;
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          position: props.variant === "expanded" ? "relative" : "fixed",
          width: drawerWidth,
          boxSizing: "border-box",
          border: "none",
        },
      }}
    >
      <DrawerNavigationContext.Provider
        value={{
          value: props.value,
          onChange: props.onChange,
          variant: props.variant,
        }}
      >
        <List>{props.children}</List>
      </DrawerNavigationContext.Provider>
    </Drawer>
  );
};

type DrawerNavigationActionProps = React.PropsWithChildren<{
  label: string;
  icon: IconName;
  value: string;
}>;

const DrawerNavigationAction: React.FC<DrawerNavigationActionProps> = (
  props
) => {
  const context = React.useContext(DrawerNavigationContext);

  if (!context) {
    throw new Error(
      "DrawerNavigationAction must be used within a DrawerNavigation"
    );
  }

  const selected = context?.value === props.value;

  return (
    <ListItem disablePadding>
      <ListItemButton
        onClick={() => context.onChange(props.value)}
        selected={selected}
        icon={props.icon}
        label={props.label}
      />
    </ListItem>
  );
};

export { DrawerNavigation, DrawerNavigationAction };
