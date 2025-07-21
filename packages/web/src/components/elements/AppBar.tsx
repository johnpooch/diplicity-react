import React from "react";
import { createUseStyles } from "../utils/styles";
import { Stack, Typography, SxProps, Theme } from "@mui/material";

type AppBarProps = {
  title?: string | React.ReactNode;
  leftButton?: React.ReactNode;
  rightButton?: React.ReactNode;
  sx?: SxProps<Theme>;
};

const useStyles = createUseStyles<AppBarProps>(() => ({
  root: {
    flexGrow: 1,
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

const AppBar: React.FC<AppBarProps> = props => {
  const styles = useStyles(props);

  const mergedSx = { ...styles.root, ...props.sx } as SxProps<Theme>;

  return (
    <Stack sx={mergedSx}>
      <Stack flexDirection="row" alignItems="center" gap={1} flexGrow={1}>
        {props.leftButton}
        {typeof props.title === "string" ? (
          <Typography variant="h1">{props.title}</Typography>
        ) : (
          props.title
        )}
      </Stack>
      {props.rightButton}
    </Stack>
  );
};

export { AppBar };
