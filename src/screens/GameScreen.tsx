import React from "react";

import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Fab,
  Modal,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Add as AddIcon,
} from "@mui/icons-material";
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
import { CreateOrder } from "../components/CreateOrder";
import { Orders } from "../components/Orders";

type Tabs = "map" | "orders" | "players";

const modalBoxStyle = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

const MapScreen: React.FC<{
  gameId: string;
}> = (props) => {
  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
  const getGameQuery = service.endpoints.getGame.useQuery(props.gameId);
  const listPhasesQuery = service.endpoints.listPhases.useQuery(props.gameId);
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

  const newestPhaseMeta = getGameQuery.data.NewestPhaseMeta;
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

  return <div dangerouslySetInnerHTML={{ __html: xml }} />;
};

const GameScreen: React.FC<{
  onClickBack: () => void;
}> = (props) => {
  const params = useParams<{ gameId: string }>();
  if (!params.gameId) throw new Error("Game ID not found");
  const [tab, setTab] = React.useState<Tabs>("map");

  const [orderCreationOpen, setOrderCreationOpen] = React.useState(false);

  const onClickCreateOrder = () => {
    setOrderCreationOpen(true);
  };

  return (
    <PageWrapper>
      <Fab
        color="primary"
        aria-label="back"
        sx={{ position: "fixed", top: 16, left: 16 }}
        onClick={props.onClickBack}
      >
        <ArrowBackIcon />
      </Fab>
      {/* <div dangerouslySetInnerHTML={{ __html: xml }} />
      <Fab
        color="primary"
        aria-label="create-order"
        sx={{ position: "fixed", bottom: 16 + 50, right: 16 }}
        onClick={props.onClickCreateOrder}
      >
        <AddIcon />
      </Fab> */}
      {tab === "map" && <MapScreen gameId={params.gameId} />}
      {tab === "orders" && <Orders gameId={params.gameId} />}
      <Fab
        color="primary"
        aria-label="create-order"
        sx={{ position: "fixed", bottom: 16 + 50, right: 16 }}
        onClick={onClickCreateOrder}
      >
        <AddIcon />
      </Fab>
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
      {/* Order creation modal */}
      <Modal
        open={orderCreationOpen}
        onClose={() => setOrderCreationOpen(false)}
      >
        <Box sx={modalBoxStyle}>
          <CreateOrder
            gameId={params.gameId}
            onClickClose={() => setOrderCreationOpen(false)}
          />
        </Box>
      </Modal>
    </PageWrapper>
  );
};

export { GameScreen };
