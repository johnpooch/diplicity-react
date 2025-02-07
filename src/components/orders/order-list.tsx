import {
  Stack,
  Typography,
  List,
  ListSubheader,
  Divider,
  ListItem,
  ListItemText,
} from "@mui/material";
import React from "react";
import { useOrders } from "../../common";
import { formatOrderText } from "../../util";
import { QueryContainer } from "../query-container";

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

const groupByNation = (
  orders: NonNullable<ReturnType<typeof useOrders>["query"]["data"]>["orders"]
) => {
  return orders.reduce((acc, order) => {
    if (!acc[order.nation]) {
      acc[order.nation] = [];
    }
    acc[order.nation].push(order);
    return acc;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  }, {} as Record<string, any[]>);
};

const OrderList: React.FC = () => {
  const { query } = useOrders();
  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) => {
        const groupedOrders = groupByNation(data.orders);
        return data.orders.length === 0 ? (
          <Stack sx={styles.emptyContainer}>
            <Typography>No order created during this turn</Typography>
          </Stack>
        ) : (
          <List disablePadding>
            {Object.keys(groupedOrders).map((nation) => (
              <React.Fragment key={nation}>
                <ListSubheader>{nation}</ListSubheader>
                <Divider />
                {groupedOrders[nation].map((order) => (
                  <ListItem key={order.source} divider>
                    <ListItemText
                      primary={formatOrderText(order)}
                      secondary={order.outcome && order.outcome.outcome}
                      sx={
                        order.outcome?.outcome === "Succeeded"
                          ? styles.orderListItemTextSucceeded
                          : styles.orderListItemTextFailed
                      }
                    />
                  </ListItem>
                ))}
              </React.Fragment>
            ))}
          </List>
        );
      }}
    </QueryContainer>
  );
};

export { OrderList };
