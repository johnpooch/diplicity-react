import React from "react";
import { useOrders } from "../common/hooks/useOrders";
import {
  Stack,
  Typography,
  List,
  ListSubheader,
  Divider,
  ListItem,
  ListItemText,
} from "@mui/material";
import { formatOrderText } from "../util";

const OrderList: React.FC<{
  orders: NonNullable<ReturnType<typeof useOrders>["query"]["data"]>;
}> = ({ orders }) => {
  // Reduce orders to be grouped by nation
  const ordersByNation = orders.reduce((acc, order) => {
    if (!acc[order.nation]) {
      acc[order.nation] = [];
    }
    acc[order.nation].push(order);
    return acc;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  }, {} as Record<string, any[]>);
  return orders.length === 0 ? (
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
};

export { OrderList };
