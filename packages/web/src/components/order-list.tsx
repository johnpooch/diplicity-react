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
  Box,
} from "@mui/material";
import {
  Add as CreateOrderIcon,
  CheckBoxOutlineBlank as OrdersNotConfirmedIcon,
  CheckBox as OrdersConfirmedIcon,
  CheckCircleOutline as SuccessIcon,
  ErrorOutline as FailureIcon,
  Assignment as NoOrdersIcon,
} from "@mui/icons-material";
import { OrderSummary } from "./order-summary";
import { useSelectedGameContext, useSelectedPhaseContext } from "../context";

const OrderList: React.FC = () => {
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

  return (
    <Stack justifyContent="space-between" sx={{ height: "100%" }}>
      <QueryContainer query={ordersListQuery} onRenderLoading={() => <></>}>
        {(orders) => (
          <>
            {orders.length === 0 ? (
              <Box sx={styles.emptyContainer}>
                <Stack spacing={2} alignItems="center">
                  <NoOrdersIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
                  <Typography variant="h6" color="text.secondary">
                    No orders created
                  </Typography>
                </Stack>
              </Box>
            ) : (
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
                          secondary={
                            order.resolution && (
                              <Stack direction="row" alignItems="center" spacing={0.5}>
                                {order.resolution.status === "Succeeded" ? (
                                  <SuccessIcon fontSize="small" color="success" />
                                ) : (
                                  <FailureIcon fontSize="small" color="error" />
                                )}
                                <Typography variant="body2" component="span">
                                  {order.resolution.status}
                                </Typography>
                              </Stack>
                            )
                          }
                          sx={
                            order.resolution?.status === "Succeeded"
                              ? styles.orderListItemTextSucceeded
                              : styles.orderListItemTextFailed
                          }
                        />
                      </ListItem>
                    ))}
                  </React.Fragment>
                ))}
              </List>
            )}
          </>
        )}
      </QueryContainer>
      <Stack>
        <Divider />
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
                onClick={() => {
                  handleConfirmOrders();
                }}
                startIcon={
                  game.phaseConfirmed ? (
                    <OrdersConfirmedIcon />
                  ) : (
                    <OrdersNotConfirmedIcon />
                  )
                }
              >
                {game.phaseConfirmed
                  ? "Orders confirmed"
                  : "Confirm orders"}
              </Button>
              <IconButton
                color="primary"
                aria-label="add"
                onClick={() => {
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
          )}
        </QueryContainer>
      </Stack>
    </Stack>
  );
};

const styles: Styles = {
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
