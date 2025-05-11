import { Stack, Fab } from "@mui/material";
import {
  Add as CreateOrderIcon,
  CheckBoxOutlineBlank as OrdersNotConfirmedIcon,
  CheckBoxOutlined as OrdersConfirmedIcon,
} from "@mui/icons-material";
import { QueryContainer } from "./query-container";
import { useNavigate } from "react-router";
import { useSelectedGameContext } from "../context";

const OrderActions: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const { query, isSubmitting, handleToggleConfirmOrders } = useOrders();
  const navigate = useNavigate();

  const handleCreateOrder = () => {
    navigate(`/game/${gameId}/orders/create`);
  };

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) => (
        <Stack sx={styles.root}>
          {data.canConfirmOrders && (
            <Fab
              color="secondary"
              aria-label="confirm orders"
              onClick={handleToggleConfirmOrders}
              disabled={isSubmitting}
              variant="extended"
            >
              {data.hasConfirmedOrders ? (
                <OrdersConfirmedIcon />
              ) : (
                <OrdersNotConfirmedIcon />
              )}
              {data.hasConfirmedOrders ? "Orders confirmed" : "Confirm orders"}
            </Fab>
          )}
          {data.canCreateOrder && (
            <Fab
              color="primary"
              aria-label="create order"
              size="medium"
              onClick={handleCreateOrder}
            >
              <CreateOrderIcon />
            </Fab>
          )}
        </Stack>
      )}
    </QueryContainer>
  );
};

const styles: Styles = {
  root: {
    flexDirection: "row",
    gap: 1,
  },
};

export { OrderActions };
