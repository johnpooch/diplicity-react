import { Outlet } from "react-router";
import { AppBar, IconButton, Stack, Toolbar, useTheme } from "@mui/material";
import { ArrowBack as BackIcon } from "@mui/icons-material";
import { PhaseSelect } from "../phase-select";
import {
  GameDetailContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";

const GameDetailsLayout: React.FC<{
  onClickBack: () => void;
  onClickCreateOrder: () => void;
  actions: React.ReactNode[];
  navigation: React.ReactNode;
  modals: React.ReactNode[];
}> = (props) => {
  const theme = useTheme();

  return (
    <GameDetailContextProvider>
      <SelectedPhaseContextProvider>
        <Stack
          sx={{
            width: "100vw",
            minHeight: "calc(100vh - 56px)",
            background: theme.palette.background.default,
            paddingBottom: "56px",
          }}
        >
          <AppBar position="static">
            <Toolbar sx={{ justifyContent: "space-between" }}>
              <IconButton
                edge="start"
                color="inherit"
                aria-label="back"
                onClick={props.onClickBack}
              >
                <BackIcon />
              </IconButton>
              <PhaseSelect />
              <Stack></Stack>
            </Toolbar>
          </AppBar>
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
      </SelectedPhaseContextProvider>
    </GameDetailContextProvider>
  );
};

export { GameDetailsLayout };
