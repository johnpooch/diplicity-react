import {
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  Stack,
} from "@mui/material";
import {
  Add as CreateOrderIcon,
  Edit as EditOrderIcon,
} from "@mui/icons-material";
import { QueryContainer } from "./query-container";
import { OrderSummary } from "./order-summary";

const OrderListCurrent: React.FC = () => {
  const query = useListCurrentOrdersQuery();
  const { setSource } = useCreateOrderContext();

  const handleCreateOrder = (province: string) => {
    setSource(province);
  };

  return (
    <Stack sx={styles.container}>
      <QueryContainer query={query} onRenderLoading={() => <></>}>
        {(data) => {
          return (
            <List disablePadding>
              <ListSubheader>Awaiting orders</ListSubheader>
              <Divider />
              {data.missingOrders.map((order) => (
                <ListItem
                  key={order.key}
                  divider
                  secondaryAction={
                    <IconButton onClick={() => handleCreateOrder(order.key)}>
                      <CreateOrderIcon />
                    </IconButton>
                  }
                >
                  <ListItemText primary={`${order.unitType} ${order.source}`} />
                </ListItem>
              ))}
              <ListSubheader>Orders</ListSubheader>
              <Divider />
              {data.orders.map((order) => (
                <ListItem
                  key={order.key}
                  divider
                  secondaryAction={
                    <IconButton onClick={() => handleCreateOrder(order.key)}>
                      <EditOrderIcon />
                    </IconButton>
                  }
                >
                  <OrderSummary {...order} />
                </ListItem>
              ))}
            </List>
          );
        }}
      </QueryContainer>
    </Stack>
  );
};

const styles: Styles = {
  container: {
    height: "100%",
  },
};

export { OrderListCurrent };
