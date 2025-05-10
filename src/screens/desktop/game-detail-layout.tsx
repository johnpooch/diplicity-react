import { AppBar, IconButton, Stack, Typography } from "@mui/material";
import { ArrowBack as BackIcon } from "@mui/icons-material";
import { Outlet, useNavigate } from "react-router";
import { GameMenu, Map, QueryContainer } from "../../components";
import { PhaseSelect } from "../../components/phase-select";
import React from "react";
import {
  SelectedGameContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";

type GameDetailLayoutProps = {
  title: string | React.ReactNode;
};

const GameDetailLayout: React.FC<GameDetailLayoutProps> = (props) => {
  console.log("GameDetailPrimaryScreenLayout");
  const navigate = useNavigate();

  const handleNavigateBack = () => {
    navigate("/");
  };

  return (
    <SelectedGameContextProvider>
      {({ gameRetrieveQuery }) => (
        <SelectedPhaseContextProvider>
          <Stack>
            <AppBar sx={styles.appBar}>
              <Stack sx={styles.backButtonTitleContainer}>
                <IconButton onClick={handleNavigateBack}>
                  <BackIcon />
                </IconButton>
                {typeof props.title === "string" ? (
                  <Typography variant="h1">{props.title}</Typography>
                ) : (
                  props.title
                )}
              </Stack>
              <PhaseSelect />
              <QueryContainer query={gameRetrieveQuery}>
                {(game) => (
                  <GameMenu
                    game={game}
                    onClickGameInfo={(navigate, gameId) => {
                      navigate(`/game/${gameId}/game-info`);
                    }}
                    onClickPlayerInfo={(navigate, gameId) => {
                      navigate(`/game/${gameId}/player-info`);
                    }}
                  />
                )}
              </QueryContainer>
            </AppBar>
            <Stack sx={styles.screen}>
              <Stack sx={styles.panelContainer}>
                <Stack sx={styles.mapPanel}>
                  <Map />
                </Stack>
                <Stack sx={styles.actionPanel}>
                  <Outlet />
                </Stack>
              </Stack>
            </Stack>
          </Stack>
        </SelectedPhaseContextProvider>
      )}
    </SelectedGameContextProvider>
  );
};

const styles: Styles = {
  appBar: {
    padding: 1,
    alignItems: "center",
    position: "relative",
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    "& h1": {
      margin: 0,
    },
  },
  backButtonTitleContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 1,
  },
  screen: {
    padding: 2,
    height: "calc(100vh - 64px)",
  },
  panelContainer: {
    width: "100%",
    height: "100%",
    flexDirection: "row",
    gap: 2,
  },
  mapPanel: {
    flex: 2,
    height: "100%",
    justifyContent: "center",
    borderRadius: 2,
    gap: 2,
  },
  actionPanel: {
    flex: 1,
    boxShadow: 4,
    borderRadius: 2,
  },
  phaseSelectContainer: {
    alignItems: "center",
  },
  mapContainer: {
    flexGrow: 1,
  },
};

export { GameDetailLayout };
