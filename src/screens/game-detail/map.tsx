import React from "react";
import { Stack, useMediaQuery, useTheme } from "@mui/material";
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
  container: {
    display: "flex",
    maxWidth: 1000,
    width: "100%",
  },
  mapContainer: {
    flex: 2,
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
    <Stack sx={styles.container}>
      <GameDetailAppBar />
      <Stack direction="row">
        <Stack sx={styles.mapContainer}>
          <QueryContainer query={mapQuery}>
            {(map) => <div dangerouslySetInnerHTML={{ __html: map }} />}
          </QueryContainer>
        </Stack>
        {!isMobile && (
          <Stack sx={styles.ordersContainer}>
            <Stack alignItems="center">
              <PhaseSelect />
            </Stack>
            <QueryContainer query={ordersQuery}>
              {(data) => <OrderList orders={data} />}
            </QueryContainer>
          </Stack>
        )}
      </Stack>
    </Stack>
  );
};

export { Map };
