import { IconButton, Stack, Typography } from "@mui/material";
import { KeyboardBackspace as BackIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";

type ScreenTopBarProps = {
  title: string;
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

const ScreenTopBar: React.FC<ScreenTopBarProps> = ({ title }) => {
  const navigate = useNavigate();

  return (
    <Stack
      spacing={2}
      direction="row"
      alignItems="center"
      padding={2}
      sx={styles.root}
    >
      <IconButton onClick={() => navigate(-1)} sx={styles.iconButton}>
        <BackIcon />
      </IconButton>
      <Typography variant="h1">{title}</Typography>
    </Stack>
  );
};

export { ScreenTopBar };
