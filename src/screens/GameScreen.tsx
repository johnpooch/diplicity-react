import React from "react";

import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Fab,
} from "@mui/material";
import { ArrowBack as ArrowBackIcon } from "@mui/icons-material";
import PageWrapper from "../components/PageWrapper";
import { useParams } from "react-router";
import {
  Map as MapIcon,
  Gavel as OrdersIcon,
  People as PlayersIcon,
} from "@mui/icons-material";
import service from "../common/store/service";
import { skipToken } from "@reduxjs/toolkit/query";
import { createMap } from "../common/map/map";

type Tabs = "map" | "orders" | "players";

const GameScreen: React.FC<{
  onClickBack: () => void;
}> = ({ onClickBack }) => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("Game ID is required");
  const [tab, setTab] = React.useState<Tabs>("map");

  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const listPhasesQuery = service.endpoints.listPhases.useQuery(gameId);
  const variantName = getGameQuery.data?.Variant;
  const getVariantMapSvgQuery = service.endpoints.getVariantSvg.useQuery(
    variantName ?? skipToken
  );
  const getVariantArmySvgQuery = service.endpoints.getVariantUnitSvg.useQuery(
    variantName ? { variantName: variantName, unitType: "Army" } : skipToken
  );
  const getVariantFleetSvgQuery = service.endpoints.getVariantUnitSvg.useQuery(
    variantName ? { variantName: variantName, unitType: "Fleet" } : skipToken
  );

  if (
    !listVariantsQuery.isSuccess ||
    !getGameQuery.isSuccess ||
    !listPhasesQuery.isSuccess ||
    !getVariantMapSvgQuery.isSuccess ||
    !getVariantArmySvgQuery.isSuccess ||
    !getVariantFleetSvgQuery.isSuccess
  ) {
    return null;
  }

  const variant = listVariantsQuery.data.find(
    (v) => v.Name === getGameQuery.data.Variant
  );
  if (!variant) throw new Error("Variant not found");

  const newestPhaseMeta = getGameQuery.data.NewestPhaseMeta
    ? getGameQuery.data.NewestPhaseMeta[0]
    : null;
  if (!newestPhaseMeta) throw new Error("Newest phase meta not found");

  const newestPhase = listPhasesQuery.data.find(
    (p) => p.PhaseOrdinal === newestPhaseMeta.PhaseOrdinal
  );

  if (!newestPhase) throw new Error("Newest phase not found");

  const xml = createMap(
    getVariantMapSvgQuery.data,
    getVariantArmySvgQuery.data,
    getVariantFleetSvgQuery.data,
    variant,
    newestPhase
  );

  return (
    <PageWrapper>
      <Fab
        color="primary"
        aria-label="back"
        sx={{ position: "fixed", top: 16, left: 16 }}
        onClick={onClickBack}
      >
        <ArrowBackIcon />
      </Fab>
      <div dangerouslySetInnerHTML={{ __html: xml }} />

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
