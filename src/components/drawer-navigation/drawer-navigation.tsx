import React from "react";
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useTheme,
} from "@mui/material";

const drawerWidth = 240;

const DrawerNavigationContext = React.createContext<
  | {
      value: string;
      onChange: (newValue: string) => void;
    }
  | undefined
>(undefined);

type DrawerNavigationProps = React.PropsWithChildren<{
  value: string;
  onChange: (newValue: string) => void;
}>;

const DrawerNavigation: React.FC<DrawerNavigationProps> = (props) => {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          position: "relative",
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
        }}
      >
        <List>{props.children}</List>
      </DrawerNavigationContext.Provider>
    </Drawer>
  );
};

type DrawerNavigationActionProps = React.PropsWithChildren<{
  label: string;
  icon: React.ReactElement;
  value: string;
}>;

const DrawerNavigationAction: React.FC<DrawerNavigationActionProps> = (
  props
) => {
  const theme = useTheme();
  const context = React.useContext(DrawerNavigationContext);

  if (!context) {
    throw new Error(
      "DrawerNavigationAction must be used within a DrawerNavigation"
    );
  }

  const selectedItemIconStyle = {
    color: theme.palette.primary.main,
  };

  const selectedItemTextStyle = {
    color: theme.palette.primary.main,
    fontWeight: "bold",
  };

  const selected = context?.value === props.value;

  return (
    <ListItem disablePadding>
      <ListItemButton onClick={() => context.onChange(props.value)}>
        <ListItemIcon>
          {React.cloneElement(props.icon, {
            style: selected ? selectedItemIconStyle : {},
          })}
        </ListItemIcon>
        <ListItemText
          primary={props.label}
          primaryTypographyProps={{
            style: selected ? selectedItemTextStyle : {},
          }}
        />
      </ListItemButton>
    </ListItem>
  );
};

export { DrawerNavigation, DrawerNavigationAction };
