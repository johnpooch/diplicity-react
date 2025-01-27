import { IconButton, Stack, Typography } from "@mui/material";
import { KeyboardBackspace as BackIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";

type ScreenTopBarProps = {
  title: string;
};

const ScreenTopBar: React.FC<ScreenTopBarProps> = ({ title }) => {
  const navigate = useNavigate();

  return (
    <Stack
      spacing={2}
      direction="row"
      alignItems="center"
      padding={2}
      sx={(theme) => ({ borderBottom: `1px solid ${theme.palette.divider}` })}
    >
      <IconButton
        onClick={() => navigate("/")}
        sx={(theme) => ({
          padding: 0,
          color: theme.palette.text.primary,
        })}
      >
        <BackIcon />
      </IconButton>
      <Typography variant="h1">{title}</Typography>
    </Stack>
  );
};

export { ScreenTopBar };
