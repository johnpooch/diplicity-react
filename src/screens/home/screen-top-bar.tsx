import { IconButton, Stack, Typography } from "@mui/material";
import { KeyboardBackspace as BackIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";

type ScreenTopBarProps = {
  title: string;
  menu?: React.ReactNode;
};

const styles: Styles = {
  root: (theme) => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
  }),
  iconButton: (theme) => ({
    padding: 0,
    color: theme.palette.text.primary,
  }),
};

const ScreenTopBar: React.FC<ScreenTopBarProps> = (props) => {
  const navigate = useNavigate();

  return (
    <Stack
      padding={2}
      sx={styles.root}
      direction="row"
      justifyContent="space-between"
    >
      <Stack direction="row" spacing={2} alignItems="center">
        <IconButton onClick={() => navigate(-1)} sx={styles.iconButton}>
          <BackIcon />
        </IconButton>
        <Typography variant="h1">{props.title}</Typography>
      </Stack>
      {props.menu}
    </Stack>
  );
};

export { ScreenTopBar };
