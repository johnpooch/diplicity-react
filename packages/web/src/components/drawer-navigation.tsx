import React from "react";
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  useTheme,
} from "@mui/material";

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
        <Stack direction="row" gap={1}>
          <ListItemIcon sx={{ minWidth: "fit-content", alignItems: "center" }}>
            {React.cloneElement(props.icon, {
              style: selected ? selectedItemIconStyle : {},
            })}
          </ListItemIcon>
          {context.variant === "expanded" && (
            <ListItemText
              primary={props.label}
              primaryTypographyProps={{
                style: selected ? selectedItemTextStyle : {},
                sx: { fontSize: 18 },
              }}
            />
          )}
        </Stack>
      </ListItemButton>
    </ListItem>
  );
};

export { DrawerNavigation, DrawerNavigationAction };
