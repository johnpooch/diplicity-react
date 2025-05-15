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
import { QueryContainer } from "./query-container";
import { OrderSummary } from "./order-summary";

const OrderListPast: React.FC = () => {
  const query = useListPastOrdersQuery();
  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) => {
        return Object.keys(data).length === 0 ? (
          <Stack sx={styles.emptyContainer}>
            <Typography>No order created during this turn</Typography>
          </Stack>
        ) : (
          <List disablePadding>
            {Object.keys(data).map((nation) => (
              <React.Fragment key={nation}>
                <ListSubheader>{nation}</ListSubheader>
                <Divider />
                {data[nation].map((order) => (
                  <ListItem key={order.source} divider>
                    <ListItemText
                      primary={<OrderSummary {...order} />}
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

export { OrderListPast };
