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
import { mergeQueries, useGetUserMemberQuery } from "../../common";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import { QueryContainer } from "../query-container";
import { useListHydratedOrdersQuery } from "../../common/hooks/useListHydratedOrdersQuery";
import { useListHydratedMissingOrdersQuery } from "../../common/hooks/useListHydratedMissingOrdersQuery";
import { useCreateOrderContext } from "../../context/create-order-context";
import { OrderSummary } from "./order-summary";

const useOrderListCurrent = () => {
  const { gameId } = useGameDetailContext();
  const { selectedPhase } = useSelectedPhaseContext();
  const getUserMemberQuery = useGetUserMemberQuery(gameId);
  const listHydratedOrdersQuery = useListHydratedOrdersQuery(
    gameId,
    selectedPhase
  );
  const listHydratedMissingOrdersQuery = useListHydratedMissingOrdersQuery(
    gameId,
    selectedPhase
  );

  const query = mergeQueries(
    [
      listHydratedOrdersQuery,
      listHydratedMissingOrdersQuery,
      getUserMemberQuery,
    ],
    (orders, missingOrders, userMember) => {
      return {
        orders: orders[userMember.Nation] ? orders[userMember.Nation] : [],
        missingOrders,
      };
    }
  );

  return { query };
};

const OrderListCurrent: React.FC = () => {
  const { query } = useOrderListCurrent();
  const { setSource } = useCreateOrderContext();

  const handleCreateOrder = (province: string) => {
    setSource(province);
  };

  return (
    <Stack sx={{ height: "100%", justifyContent: "space-between" }}>
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
                  onClick={() => handleCreateOrder(order.key)}
                  secondaryAction={
                    <IconButton >
                      <EditOrderIcon />
                    </IconButton>
                  }
                  sx={{ 
                    flexWrap: 'wrap',
                    paddingRight: '48px' // Make space for the IconButton
                  }}
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

export { OrderListCurrent };
