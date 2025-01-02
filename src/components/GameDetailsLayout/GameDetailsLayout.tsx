import { Outlet } from "react-router";
import { Fab, Stack, useTheme } from "@mui/material";
import { ArrowBack as BackIcon } from "@mui/icons-material";

const GameDetailsLayout: React.FC<{
  onClickBack: () => void;
  onClickCreateOrder: () => void;
  actions: React.ReactNode[];
  navigation: React.ReactNode;
  modals: React.ReactNode[];
}> = (props) => {
  const theme = useTheme();
  return (
    <Stack
      sx={{
        width: "100vw",
        height: "calc(100vh - 56px)",
        background: theme.palette.background.default,
      }}
    >
      <Fab
        color="primary"
        aria-label="back"
        sx={{ position: "fixed", top: 16, left: 16 }}
        onClick={props.onClickBack}
      >
        <BackIcon />
      </Fab>
      <Outlet />
      <Stack
        direction="row"
        spacing={2}
        alignItems="center"
        sx={{
          position: "fixed",
          bottom: 16 + 50,
          right: 16,
        }}
      >
        {props.actions}
      </Stack>
      {props.navigation}
      {props.modals}
    </Stack>
  );
};

export { GameDetailsLayout };
