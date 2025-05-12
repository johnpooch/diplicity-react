import React from "react";
import { QueryContainer } from "./query-container";
import { service } from "../store";
import {
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  Stack,
  Typography,
} from "@mui/material";
import {
  Add as CreateOrderIcon,
  CheckBoxOutlineBlank as OrdersNotConfirmedIcon,
  CheckBox as OrdersConfirmedIcon,
} from "@mui/icons-material";
import { OrderSummary } from "./order-summary";
import { useSelectedGameContext, useSelectedPhaseContext } from "../context";

const OrderList: React.FC = () => {
  const { gameRetrieveQuery, gameId } = useSelectedGameContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const query = service.endpoints.gamePhaseOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  const [confirmOrders, confirmOrdersMutation] =
    service.endpoints.gameConfirmCreate.useMutation();

  const handleConfirmOrders = async () => {
    await confirmOrders({ gameId }).unwrap();
  };

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {
        (orders) => {
          // const phase = game.phases.find((p) => p.id === selectedPhase);
          // if (!phase) throw new Error("Phase not found");
          // const phaseStates = phase.phaseStates;

          // const ordersByNation: Record<string, PhaseStateOrders[]> = {};

          // phaseStates.forEach((phaseState) => {
          //   const nation = phaseState.member.nation;
          //   const orders = phaseState.orders;
          //   ordersByNation[nation] = orders;
          // });

          // const variant = game.variant;
          // const getProvinceName = (provinceId: string | null) => {
          //   if (!provinceId) return undefined;
          //   const province = variant.provinces.find((p) => p.id === provinceId);
          //   if (!province) throw new Error("Province not found");
          //   return province.name;
          // };

          // const getUnitType = (provinceId: string) => {
          //   const unit = phase.units.find((u) => u.province === provinceId);
          //   return unit ? unit.type : undefined;
          // };

          return orders.length === 0 ? (
            <Stack sx={styles.emptyContainer}>
              <Typography>No order created during this turn</Typography>
            </Stack>
          ) : (
            <Stack justifyContent="space-between" sx={{ height: "100%" }}>
              <List disablePadding>
                {orders.map(({ nation, orders }) => (
                  <React.Fragment key={nation}>
                    <ListSubheader>{nation}</ListSubheader>
                    <Divider />
                    {orders.map((order) => (
                      <ListItem key={order.source} divider>
                        <ListItemText
                          primary={
                            <OrderSummary
                              source={order.source}
                              destination={order.target}
                              aux={order.aux}
                              type={order.orderType}
                              unitType={"Army"}
                            />
                          }
                        // secondary={order.outcome && order.outcome.outcome}
                        // sx={
                        //   order.outcome?.outcome === "Succeeded"
                        //     ? styles.orderListItemTextSucceeded
                        //     : styles.orderListItemTextFailed
                        // }
                        />
                      </ListItem>
                    ))}
                  </React.Fragment>
                ))}
              </List>
              <Stack>
                <Divider />
                <Stack
                  gap={1}
                  direction="row"
                  alignItems={"center"}
                  p={1}
                  justifyContent={"flex-end"}
                >
                  <Button
                    variant="contained"
                    size="medium"
                    disabled={confirmOrdersMutation.isLoading}
                    onClick={() => {
                      handleConfirmOrders();
                    }}
                  // startIcon={
                  //   game.ordersConfirmed ? (
                  //     <OrdersConfirmedIcon />
                  //   ) : (
                  //     <OrdersNotConfirmedIcon />
                  //   )
                  // }
                  >
                    {/* {game.ordersConfirmed
                      ? "Orders confirmed"
                      : "Confirm orders"} */}
                  </Button>
                  <IconButton
                    color="primary"
                    aria-label="add"
                    onClick={() => {
                      // Handle button click
                    }}
                    sx={{
                      backgroundColor: "primary.main",
                      color: "secondary.main",
                      "&:hover": {
                        backgroundColor: "primary.dark",
                      },
                    }}
                  >
                    <CreateOrderIcon />
                  </IconButton>
                </Stack>
              </Stack>
            </Stack>
          );
        }
        // data.PhaseOrdinal === selectedPhase ? (
        //   <OrderListCurrent />
        // ) : (
        //   <OrderListPast />
        // )
      }
    </QueryContainer>
  );
};

const styles: Styles = {
  emptyContainer: {
    padding: 2,
    alightItems: "center",
    height: "100%",
    "& .MuiTypography-root": {
      textAlign: "center",
    },
  },
  orderListItemTextSucceeded: (theme) => ({
    "& .MuiListItemText-secondary": {
      color: theme.palette.success.main,
    },
  }),
  orderListItemTextFailed: (theme) => ({
    "& .MuiListItemText-secondary": {
      color: theme.palette.error.main,
    },
  }),
};

export { OrderList };
