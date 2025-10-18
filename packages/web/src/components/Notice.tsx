import React from "react";
import { Box, Typography, SxProps, Theme } from "@mui/material";
import { createUseStyles } from "./utils/styles";
import { Icon, IconName } from "./Icon";

interface NoticeProps {
  icon?: IconName;
  title: string;
  message?: string | React.ReactNode;
  sx?: SxProps<Theme>;
}

const useStyles = createUseStyles<NoticeProps>((props, theme) => ({
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: theme.spacing(4),
    textAlign: "center",
    minHeight: 250,
    ...props.sx,
  },
  icon: {
    height: 32,
    width: 32,
    marginBottom: theme.spacing(3),
    opacity: 0.6,
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    color: theme.palette.text.primary,
    marginBottom: theme.spacing(1),
  },
  message: {
    fontSize: 16,
    color: theme.palette.text.secondary,
    maxWidth: 400,
    lineHeight: 1.5,
    textAlign: "center",
  },
}));

const Notice: React.FC<NoticeProps> = props => {
  const styles = useStyles(props);

  return (
    <Box sx={styles.container}>
      {props.icon && <Icon name={props.icon} sx={styles.icon} />}
      <Typography sx={styles.title}>{props.title}</Typography>
      {props.message &&
        (typeof props.message === "string" ? (
          <Typography sx={styles.message}>{props.message}</Typography>
        ) : (
          props.message
        ))}
    </Box>
  );
};

export { Notice };
