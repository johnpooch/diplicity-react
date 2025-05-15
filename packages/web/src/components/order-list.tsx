import React, { useState } from "react";
import { QueryContainer } from "./query-container";
import { orderSlice, service } from "../store";
import {
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  ListSubheader,
  Stack,
  Typography,
  Box,
} from "@mui/material";
import {
  Add as CreateOrderIcon,
  CheckBoxOutlineBlank as OrdersNotConfirmedIcon,
  CheckBox as OrdersConfirmedIcon,
  Assignment as NoOrdersIcon,
} from "@mui/icons-material";
import { OrderSummary } from "./order-summary";
import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { CreateOrder } from "./create-order";
import { useDispatch } from "react-redux";

interface Orderable {
  province?: string;
  provinceId: string;
  unitType?: string;
  order?: {
    target?: string;
    aux?: string;
    orderType?: string;
    resolution?: {
      status?: string;
      by?: string;
    };
  }
}

const OrderList: React.FC = () => {
  const dispatch = useDispatch();
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const { gameRetrieveQuery, gameId } = useSelectedGameContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const ordersListQuery = service.endpoints.gamePhaseOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  const [confirmOrders, confirmOrdersMutation] =
    service.endpoints.gameConfirmCreate.useMutation();

  const handleConfirmOrders = async () => {
    await confirmOrders({ gameId }).unwrap();
  };

  const handleCreateOrderForProvince = (provinceId: string) => {
    dispatch(orderSlice.actions.resetOrder());
    dispatch(orderSlice.actions.updateOrder(provinceId));
    setShowCreateOrder(true);
  };

  return (
    <QueryContainer query={gameRetrieveQuery} onRenderLoading={() => <></>}>
      {(game) => (
        <Stack justifyContent="space-between" sx={{ height: "100%" }}>
          <QueryContainer query={ordersListQuery} onRenderLoading={() => <></>}>
            {(ordersList) => {
              const isCurrentPhase = game.currentPhase.id === selectedPhase;
              const phase = game.phases.find(p => p.id === selectedPhase);
              if (!phase) return null;

              const userNation = game.members.find(m => m.isCurrentUser)?.nation;
              const provinces = game.variant.provinces;

              const orderablesByNation = new Map<string, Orderable[]>();
              phase.options.filter((no) => {
                if (isCurrentPhase) {
                  return no.nation === userNation;
                }
                return true;
              }).forEach(nationOptions => {
                const orderables: Orderable[] = [];
                const { nation, options } = nationOptions;
                const sources = Object.keys(options);
                const nationOrders = ordersList.find(o => o.nation === nation);
                if (!nationOrders) return;
                sources.forEach(source => {
                  const order = nationOrders.orders.find(o => o.source === source);
                  const orderable: Orderable = {
                    province: provinces.find(p => p.id === source)?.name as string,
                    provinceId: source,
                    unitType: phase.units.find(u => u.province.id === source)?.type,
                    order: order?.source ? {
                      target: provinces.find(p => p.id === order?.target)?.name ?? undefined,
                      aux: provinces.find(p => p.id === order?.aux)?.name ?? undefined,
                      orderType: order?.orderType ?? undefined,
                      resolution: order?.resolution ? {
                        status: order?.resolution?.status ?? undefined,
                        by: provinces.find(p => p.id === order?.resolution?.by)?.name ?? undefined,
                      } : undefined,
                    } : undefined,
                  }
                  orderables.push(orderable);
                })
                orderablesByNation.set(nation, orderables);
              })

              return (
                <List disablePadding>
                  {Array.from(orderablesByNation.entries()).map(([nation, orderables]) => (
                    <React.Fragment key={nation}>
                      <ListSubheader>{nation}</ListSubheader>
                      <Divider />
                      {orderables.map((orderable) => (
                        <ListItem
                          key={orderable.province}
                          divider
                          sx={styles.listItem}
                        >
                          <ListItemText
                            primary={
                              orderable.order ? (
                                <OrderSummary
                                  source={orderable.province as string}
                                  destination={orderable.order.target}
                                  aux={orderable.order.aux}
                                  type={orderable.order.orderType}
                                />
                              ) : (
                                <Typography variant="body1">
                                  {orderable.unitType?.charAt(0).toUpperCase() + orderable.unitType?.slice(1)} {orderable.province}
                                </Typography>
                              )
                            }
                            secondary={
                              orderable.order && orderable.order.resolution ? (
                                <Typography
                                  variant="body2"
                                  sx={orderable.order.resolution.status === 'Succeeded' ? styles.orderListItemTextSucceeded : styles.orderListItemTextFailed}
                                >
                                  {orderable.order.resolution.status}
                                </Typography>
                              ) : (
                                <Typography
                                  variant="body2"
                                  sx={styles.noOrderText}
                                >
                                  No order issued
                                </Typography>
                              )
                            }
                          />
                          {isCurrentPhase && (
                            <ListItemSecondaryAction>
                              <IconButton
                                edge="end"
                                onClick={() => handleCreateOrderForProvince(orderable.provinceId)}
                                size="small"
                              >
                                <CreateOrderIcon />
                              </IconButton>
                            </ListItemSecondaryAction>
                          )}
                        </ListItem>
                      ))}
                    </React.Fragment>
                  ))}
                </List>
              );
            }}
          </QueryContainer>
          <Stack>
            <Divider />
            {showCreateOrder ? (
              <CreateOrder onClose={() => setShowCreateOrder(false)} />
            ) : (
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
                  onClick={handleConfirmOrders}
                  startIcon={
                    game.phaseConfirmed ? (
                      <OrdersConfirmedIcon />
                    ) : (
                      <OrdersNotConfirmedIcon />
                    )
                  }
                >
                  {game.phaseConfirmed ? "Orders confirmed" : "Confirm orders"}
                </Button>
              </Stack>
            )}
          </Stack>
        </Stack>
      )}
    </QueryContainer>
  );
};

const styles = {
  emptyContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    padding: 2,
    "& .MuiTypography-root": {
      textAlign: "center",
    },
  },
  listItem: {
    py: 1,
  },
  noOrderText: {
    color: 'text.secondary',
    mt: 0.5,
  },
  orderListItemTextSucceeded: (theme: any) => ({
    color: theme.palette.success.main,
  }),
  orderListItemTextFailed: (theme: any) => ({
    color: theme.palette.error.main,
  }),
} as const;

export { OrderList };
