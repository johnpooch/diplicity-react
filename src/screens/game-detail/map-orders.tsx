import React from "react";
import {
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Stack,
} from "@mui/material";
import {
  CheckCircle as OrderOkIcon,
  Cancel as OrderErrorIcon,
} from "@mui/icons-material";
import { PhaseSelect } from "../../components/phase-select";
import { formatOrderText } from "../../util";
import { useOrders } from "../../components/orders/use-orders";

const styles: Styles = {
  container: {
    display: "flex",
  },
  mapContainer: {
    flex: 2,
    borderRight: "1px solid #ccc",
  },
  ordersContainer: {
    flex: 1,
  },
  mapImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
};

const MapOrders: React.FC = () => {
  const { orders } = useOrders();

  return (
    <Stack sx={styles.container} direction={"row"}>
      <Stack sx={styles.mapContainer}>
        <img
          src="https://diplicity-engine.appspot.com/Variant/Classical/Map.svg"
          alt="Game Map"
        />
      </Stack>
      <Stack sx={styles.ordersContainer}>
        <Stack sx={{ p: 1 }}>
          <PhaseSelect />
        </Stack>
        <Divider />
        <List disablePadding>
          {orders?.map(({ nation, orders }) => (
            <List
              disablePadding
              key={nation}
              subheader={
                <ListSubheader
                  sx={(theme) => ({
                    borderBottom: `1px solid ${theme.palette.divider}`,
                  })}
                >
                  {nation}
                </ListSubheader>
              }
            >
              {orders.map((order, index) => (
                <ListItem key={index} divider>
                  {order.outcome && (
                    <ListItemIcon>
                      {order.outcome.outcome === "Succeeded" ? (
                        <OrderOkIcon
                          sx={(theme) => ({
                            color: theme.palette.success.main,
                          })}
                        />
                      ) : (
                        <OrderErrorIcon
                          sx={(theme) => ({ color: theme.palette.error.main })}
                        />
                      )}
                    </ListItemIcon>
                  )}
                  <ListItemText
                    primary={formatOrderText(order)}
                    secondary={order.outcome && order.outcome.outcome}
                  />
                </ListItem>
              ))}
            </List>
          ))}
        </List>
      </Stack>
    </Stack>
  );
};

export { MapOrders };
