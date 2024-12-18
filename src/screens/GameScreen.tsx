import React from "react";

import {
  Typography,
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
} from "@mui/material";
import PageWrapper from "../components/PageWrapper";
import { useParams } from "react-router";
import {
  Map as MapIcon,
  Gavel as OrdersIcon,
  People as PlayersIcon,
} from "@mui/icons-material";
import service from "../common/store/service";

type Tabs = "map" | "orders" | "players";

const GameScreen: React.FC = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("Game ID is required");
  const [tab, setTab] = React.useState<Tabs>("map");
  service.endpoints.getGame.useQuery(gameId);
  return (
    <PageWrapper>
      <Typography variant="h4">Game {gameId}</Typography>

      <AppBar position="fixed" color="primary" sx={{ top: "auto", bottom: 0 }}>
        <BottomNavigation
          value={tab}
          onChange={(_event, newValue) => {
            setTab(newValue);
          }}
        >
          <BottomNavigationAction label="Map" icon={<MapIcon />} value="map" />
          <BottomNavigationAction
            label="Orders"
            icon={<OrdersIcon />}
            value="orders"
          />
          <BottomNavigationAction
            label="Players"
            icon={<PlayersIcon />}
            value="players"
          />
        </BottomNavigation>
      </AppBar>
    </PageWrapper>
  );
};

export { GameScreen };
