import React from "react";
import {
  Divider,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  Stack,
  Typography,
} from "@mui/material";
import { formatOrderText } from "../../util";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import {
  mergeQueries,
  useGetOrdersQuery,
  useGetPhaseQuery,
  useGetVariantQuery,
} from "../../common";
import { QueryContainer } from "../../components";
import { GameDetailAppBar } from "./app-bar";

const styles: Styles = {
  container: (theme) => ({
    display: "flex",
    border: `1px solid ${theme.palette.divider}`,
  }),
  ordersContainer: {
    flex: 1,
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
          nation: order.Nation,
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

const Orders: React.FC = () => {
  const { query } = useOrders();

  return (
    <Stack sx={styles.container} direction={"row"}>
      <Stack sx={styles.ordersContainer}>
        <GameDetailAppBar />
        <Divider />
        <QueryContainer query={query}>
          {(data) => {
            // Reduce orders to be grouped by nation
            const ordersByNation = data.reduce((acc, order) => {
              if (!acc[order.nation]) {
                acc[order.nation] = [];
              }
              acc[order.nation].push(order);
              return acc;
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
            }, {} as Record<string, any[]>);
            return data.length === 0 ? (
              <Stack p={2} alignItems="center" sx={{ height: "100%" }}>
                <Typography>No order created during this turn</Typography>
              </Stack>
            ) : (
              <List disablePadding>
                {Object.keys(ordersByNation).map((nation) => (
                  <React.Fragment key={nation}>
                    <ListSubheader>{nation}</ListSubheader>
                    <Divider />
                    {ordersByNation[nation].map((order) => (
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
                  </React.Fragment>
                ))}
              </List>
            );
          }}
        </QueryContainer>
      </Stack>
    </Stack>
  );
};

export { Orders };
