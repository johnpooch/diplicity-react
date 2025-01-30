import React from "react";
import { Divider, Stack, useMediaQuery, useTheme } from "@mui/material";
import { PhaseSelect } from "../../components/phase-select";
import { OrderList, QueryContainer } from "../../components";
import { GameDetailAppBar } from "./app-bar";
import {
  mergeQueries,
  useGetMapSvgQuery,
  useGetPhaseQuery,
  useGetUnitSvgQuery,
  useGetVariantQuery,
  useOrders,
} from "../../common";
import { createMap } from "../../common/map/map";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";

const styles: Styles = {
  container: (theme) => ({
    display: "flex",
    border: `1px solid ${theme.palette.divider}`,
  }),
  mapContainer: {
    flex: 2,
    borderRight: "1px solid #ccc",
  },
  ordersContainer: {
    flex: 1,
  },
  mapImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
};

const useMap = () => {
  const { gameId } = useGameDetailContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const getVariantQuery = useGetVariantQuery(gameId);
  const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
  const getMapSvgQuery = useGetMapSvgQuery(gameId);
  const getArmySvgQuery = useGetUnitSvgQuery(gameId, "Army");
  const getFleetSvgQuery = useGetUnitSvgQuery(gameId, "Fleet");

  const query = mergeQueries(
    [
      getVariantQuery,
      getPhaseQuery,
      getMapSvgQuery,
      getArmySvgQuery,
      getFleetSvgQuery,
    ],
    (variant, phase, mapSvg, armySvg, fleetSvg) => {
      return createMap(mapSvg, armySvg, fleetSvg, variant, phase);
    }
  );
  return { query };
};

const Map: React.FC = () => {
  const { query: ordersQuery } = useOrders();
  const { query: mapQuery } = useMap();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <Stack sx={styles.container} direction={isMobile ? "column" : "row"}>
      {isMobile && <GameDetailAppBar />}
      <Stack sx={styles.mapContainer}>
        <QueryContainer query={mapQuery}>
          {(map) => <div dangerouslySetInnerHTML={{ __html: map }} />}
        </QueryContainer>
      </Stack>
      {!isMobile && (
        <Stack sx={styles.ordersContainer}>
          <Stack sx={{ p: 1 }}>
            <PhaseSelect />
          </Stack>
          <Divider />
          <QueryContainer query={ordersQuery}>
            {(data) => <OrderList orders={data} />}
          </QueryContainer>
        </Stack>
      )}
    </Stack>
  );
};

export { Map };
