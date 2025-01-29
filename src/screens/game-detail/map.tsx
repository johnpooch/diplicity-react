import React from "react";
import {
  Divider,
  List,
  ListItem,
  ListItemText,
  Stack,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { PhaseSelect } from "../../components/phase-select";
import { formatOrderText } from "../../util";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import {
  mergeQueries,
  useGetOrdersQuery,
  useGetPhaseQuery,
  useGetVariantQuery,
} from "../../common";
import { QueryContainer } from "../../components";

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

const useOrders = () => {
  const { gameId } = useGameDetailContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const getVariantQuery = useGetVariantQuery(gameId);
  const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
  const listOrdersQuery = useGetOrdersQuery(gameId, selectedPhase);

  const query = mergeQueries(
    [getVariantQuery, getPhaseQuery, listOrdersQuery],
    (variant, phase, orders) => {
      return orders.Orders.map((order) => {
        const [source, orderType, target, aux] = order.Parts;
        if (!source) throw new Error("No source found");
        if (!orderType) throw new Error("No orderType found");
        const outcome = phase.Resolutions?.find(
          (resolution) => resolution.province === source
        );

        return {
          source: variant.getProvinceLongName(source),
          orderType: orderType,
          target: target ? variant.getProvinceLongName(target) : undefined,
          aux: aux ? variant.getProvinceLongName(aux) : undefined,
          outcome: outcome
            ? {
                outcome: outcome.outcome,
                by: outcome.by
                  ? variant.getProvinceLongName(outcome.by)
                  : undefined,
              }
            : undefined,
        };
      });
    }
  );

  return { query };
};

const Map: React.FC = () => {
  const { query } = useOrders();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <Stack sx={styles.container} direction={"row"}>
      <Stack sx={styles.mapContainer}>
        <img
          src="https://diplicity-engine.appspot.com/Variant/Classical/Map.svg"
          alt="Game Map"
        />
      </Stack>
      {!isMobile && (
        <Stack sx={styles.ordersContainer}>
          <Stack sx={{ p: 1 }}>
            <PhaseSelect />
          </Stack>
          <Divider />
          <QueryContainer query={query}>
            {(data) => (
              <List disablePadding>
                {data.map((order) => (
                  <ListItem key={order.source} divider>
                    <ListItemText
                      primary={formatOrderText(order)}
                      secondary={order.outcome && order.outcome.outcome}
                      sx={(theme) => ({
                        "& .MuiListItemText-secondary": {
                          color:
                            order.outcome?.outcome === "Succeeded"
                              ? theme.palette.success.main
                              : theme.palette.error.main,
                        },
                      })}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </QueryContainer>
        </Stack>
      )}
    </Stack>
  );
};

export { Map };
