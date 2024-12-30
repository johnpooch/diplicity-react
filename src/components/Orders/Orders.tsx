import React from "react";
import {
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Stack,
  Typography,
} from "@mui/material";

import { useOrders } from "./Orders.hook";

type OrderProps = {
  source: string;
  orderType: string;
  unitTypeSvg: string;
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
    <Stack spacing={2}>
      {orders.map(({ nation, orders }) => (
        <Stack spacing={2} key={nation}>
          <List subheader={<ListSubheader>{nation}</ListSubheader>}>
            {orders.map((order, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <img src={order.unitTypeSvg} style={{ width: 32 }} />
                </ListItemIcon>
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
