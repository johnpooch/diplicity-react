import React from "react";
import { Fab, Grid2, Stack } from "@mui/material";
import { ArrowBack as BackIcon } from "@mui/icons-material";
import { Outlet, useNavigate } from "react-router";
import {
  GameDetailContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";

const styles: Styles = {
  fab: {
    position: "fixed",
    top: 16,
    left: 16,
  },
  largeRoot: {
    alignItems: "center",
  },
  largeContentContainer: {
    p: 4,
    display: "flex",
    justifyContent: "center",
    flexGrow: 1,
    maxWidth: 1000,
    width: "100%",
  },
  contentContainer: (theme) => ({
    width: "100%",
    border: `1px solid ${theme.palette.divider}`,
  }),
};

const GameDetailLayout: React.FC = () => {
  const navigate = useNavigate();
  return (
    <GameDetailContextProvider>
      <SelectedPhaseContextProvider>
        {/* Top left Fab */}
        <Fab sx={styles.fab} onClick={() => navigate("/")}>
          <BackIcon />
        </Fab>

        <Stack sx={styles.largeRoot}>
          <Grid2 container sx={styles.largeContentContainer}>
            <Grid2 size="grow">
              <Stack sx={{ alignItems: "center" }}>
                <Stack sx={styles.contentContainer}>
                  <Outlet />
                </Stack>
              </Stack>
            </Grid2>
          </Grid2>
        </Stack>
      </SelectedPhaseContextProvider>
    </GameDetailContextProvider>
  );
};

export { GameDetailLayout };
