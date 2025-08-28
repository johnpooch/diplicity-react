import { Drawer, List, ListItem } from "@mui/material";
import { IconName } from "./Icon";
import { createUseStyles } from "./utils/styles";
import { ListItemButton } from "./Button";
import { useMatch } from "react-router";
import React from "react";

interface SideNavigationProps {
  options: {
    label: string;
    icon: IconName;
    path: string;
    onClick: () => void;
  }[];
  variant: "expanded" | "collapsed";
}

const useStyles = createUseStyles<SideNavigationProps>(props => ({
  root: {
    width: props.variant === "expanded" ? 240 : 56,
    flexShrink: 0,
    "& .MuiDrawer-paper": {
      position: props.variant === "expanded" ? "relative" : "fixed",
      boxSizing: "border-box",
      border: "none",
    },
  },
}));

const useItemStyles = createUseStyles<{
  selected: boolean;
  variant: "expanded" | "collapsed";
}>(props => ({
  root: theme => ({
    backgroundColor: props.selected ? "rgba(0, 0, 0, 0.08)" : "transparent",
    color: props.selected ? theme.palette.primary.main : undefined,
  }),
}));

const SideNavigationItem: React.FC<{
  option: {
    label: string;
    icon: IconName;
    path: string;
    onClick: () => void;
  };
  variant: "expanded" | "collapsed";
}> = props => {
  const match = useMatch(props.option.path);
  const selected = match !== null;

  const styles = useItemStyles({ selected, variant: props.variant });

  return (
    <ListItem disablePadding>
      {props.variant === "expanded" ? (
        <ListItemButton
          sx={styles.root}
          selected={selected}
          onClick={props.option.onClick}
          icon={props.option.icon}
          label={props.option.label}
          aria-label={props.option.label}
        />
      ) : (
        <ListItemButton
          sx={styles.root}
          selected={selected}
          icon={props.option.icon}
          onClick={props.option.onClick}
          aria-label={props.option.label}
        />
      )}
    </ListItem>
  );
};

const SideNavigation: React.FC<SideNavigationProps> = props => {
  const styles = useStyles(props);

  return (
    <Drawer variant="permanent" sx={styles.root}>
      <List>
        {props.options.map(option => (
          <React.Fragment key={option.path}>
            <SideNavigationItem
              option={option}
              variant={props.variant}
            />
          </React.Fragment>
        ))}
      </List>
    </Drawer>
  );
};

export { SideNavigation };
