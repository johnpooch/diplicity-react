import React from "react";
import {
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  Stack,
  Typography,
} from "@mui/material";

import { useOrders } from "./Orders.hook";

type OrderProps = {
  source: string;
  orderType: string;
  target?: string;
  aux?: string;
};

const formatOrderText = (order: OrderProps) => {
  if (order.orderType === "Hold") {
    return `${order.source} Hold`;
  }
  if (order.orderType === "Support") {
    return `${order.source} Support ${order.target} ${order.aux}`;
  }
  return `${order.source} ${order.orderType} to ${order.target}`;
};

const Orders: React.FC = () => {
  const { isLoading, isError, orders } = useOrders();

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <CircularProgress />
      </Stack>
    );
  }

  if (isError) {
    return (
      <Stack spacing={2}>
        <Typography>Error loading orders</Typography>
      </Stack>
    );
  }

  return (
    <Stack
      spacing={2}
      padding={2}
      sx={{ maxWidth: 630, width: "100%", margin: "0 auto" }}
    >
      <Typography variant="h1">Orders</Typography>
      {orders.map(({ nation, orders }) => (
        <Stack spacing={2} key={nation}>
          <List
            subheader={
              <ListSubheader
                sx={{
                  textAlign: "left",
                  fontWeight: "bold",
                }}
              >
                {nation}
              </ListSubheader>
            }
          >
            {orders.map((order, index) => (
              <ListItem key={index}>
                <ListItemText>{formatOrderText(order)}</ListItemText>
              </ListItem>
            ))}
          </List>
        </Stack>
      ))}
    </Stack>
  );
};

export { Orders };
