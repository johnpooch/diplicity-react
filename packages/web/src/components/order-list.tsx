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
import { Unit, Order, Phase } from "../store/service";
import { CreateOrder } from "./create-order";
import { useDispatch } from "react-redux";
interface UnitWithOrder {
  unit: Unit;
  order?: Order;
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

  // Group units by nation and match with their orders
  const getUnitsWithOrders = (phase: Phase, orders: Order[], isCurrentPhase: boolean, userNation?: string) => {
    const unitsByNation = new Map<string, UnitWithOrder[]>();

    // Filter units based on whether it's current phase and user's nation
    const relevantUnits = phase.units.filter(unit => {
      if (isCurrentPhase) {
        return unit.nation.name === userNation;
      }
      return true;
    });

    // Group units by nation and match with orders
    relevantUnits.forEach(unit => {
      const nationName = unit.nation.name;
      if (!unitsByNation.has(nationName)) {
        unitsByNation.set(nationName, []);
      }

      const order = orders.find(o => o.source === unit.province.id);
      unitsByNation.get(nationName)?.push({ unit, order });
    });

    return unitsByNation;
  };

  return (
    <Stack justifyContent="space-between" sx={{ height: "100%" }}>
      <QueryContainer query={ordersListQuery} onRenderLoading={() => <></>}>
        {(ordersList) => (
          <QueryContainer query={gameRetrieveQuery} onRenderLoading={() => <></>}>
            {(game) => {
              const currentPhase = game.currentPhase;
              const isCurrentPhase = currentPhase.id === selectedPhase;
              const userNation = game.members.find(m => m.isCurrentUser)?.nation;

              // Flatten orders from all nations into a single array
              const allOrders = ordersList.flatMap(no => no.orders);

              // Get the phase we're viewing
              const viewingPhase = isCurrentPhase ? currentPhase :
                game.phases.find(p => p.id === selectedPhase);

              if (!viewingPhase) return null;

              const unitsByNation = getUnitsWithOrders(
                viewingPhase,
                allOrders,
                isCurrentPhase,
                userNation
              );

              if (unitsByNation.size === 0) {
                return (
                  <Box sx={styles.emptyContainer}>
                    <Stack spacing={2} alignItems="center">
                      <NoOrdersIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
                      <Typography variant="h6" color="text.secondary">
                        No units found
                      </Typography>
                    </Stack>
                  </Box>
                );
              }

              return (
                <List disablePadding>
                  {Array.from(unitsByNation.entries()).map(([nation, unitsWithOrders]) => (
                    <React.Fragment key={nation}>
                      <ListSubheader>{nation}</ListSubheader>
                      <Divider />
                      {unitsWithOrders.map(({ unit, order }) => (
                        <ListItem
                          key={unit.province.id}
                          divider
                          sx={styles.listItem}
                        >
                          <ListItemText
                            primary={
                              <Typography variant="body1">
                                {unit.type} {unit.province.name}
                              </Typography>
                            }
                            secondary={
                              order ? (
                                <OrderSummary
                                  source={order.source}
                                  destination={order.target}
                                  aux={order.aux}
                                  type={order.orderType}
                                />
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
                                onClick={() => handleCreateOrderForProvince(unit.province.id)}
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
        )}
      </QueryContainer>
      <Stack>
        <Divider />
        {showCreateOrder ? (
          <CreateOrder onClose={() => setShowCreateOrder(false)} />
        ) : (
          <QueryContainer query={gameRetrieveQuery} onRenderLoading={() => <></>}>
            {(game) => (
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
          </QueryContainer>
        )}
      </Stack>
    </Stack>
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
    "& .MuiListItemText-secondary": {
      color: theme.palette.success.main,
    },
  }),
  orderListItemTextFailed: (theme: any) => ({
    "& .MuiListItemText-secondary": {
      color: theme.palette.error.main,
    },
  }),
} as const;

export { OrderList };
