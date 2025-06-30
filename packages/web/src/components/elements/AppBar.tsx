import React from "react";
import { createUseStyles } from "../utils/styles";
import { Stack, Typography } from "@mui/material";

type AppBarProps = {
  title?: string;
  leftButton?: React.ReactNode;
  rightButton?: React.ReactNode;
};

const useStyles = createUseStyles<AppBarProps>(() => ({
  root: {
    minHeight: 56,
    flexDirection: "row",
    alignItems: "center",
    padding: 1,
    justifyContent: "space-between",
    gap: 1,
    "& h1": {
      margin: 0,
    },
  },
}));

const AppBar: React.FC<AppBarProps> = (props) => {
  const styles = useStyles(props);

  return (
    <Stack sx={styles.root}>
      <Stack flexDirection="row" alignItems="center" gap={1}>
        {props.leftButton}
        <Typography variant="h1">{props.title}</Typography>
      </Stack>
      {props.rightButton}
    </Stack>
  );
};

export { AppBar };
