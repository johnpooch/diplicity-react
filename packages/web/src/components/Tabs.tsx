import React from "react";
import {
  Tabs as MuiTabs,
  Tab as MuiTab,
  TabsProps as MuiTabsProps,
} from "@mui/material";
import { createUseStyles } from "./utils/styles";

interface TabOption {
  value: string;
  label: string;
  icon?: React.ReactElement;
}

interface TabsProps extends Omit<MuiTabsProps, "children"> {
  options: TabOption[];
}

const useStyles = createUseStyles<TabsProps>(() => ({
  root: {
    width: "100%",
  },
}));

const Tabs: React.FC<TabsProps> = props => {
  const styles = useStyles(props);
  const { options, ...rest } = props;

  return (
    <MuiTabs variant="fullWidth" sx={styles.root} {...rest}>
      {options.map(option => (
        <MuiTab
          key={option.value}
          disableRipple
          value={option.value}
          label={option.label}
          icon={option.icon}
          iconPosition="start"
        />
      ))}
    </MuiTabs>
  );
};

export { Tabs };
export type { TabOption, TabsProps };
