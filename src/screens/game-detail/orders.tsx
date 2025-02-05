import React, { useState } from "react";
import { Stack, Fab, Modal, Box } from "@mui/material";
import {
  Add as CreateOrderIcon,
  CheckBoxOutlineBlank as OrdersNotConfirmedIcon,
  CheckBoxOutlined as OrdersConfirmedIcon,
} from "@mui/icons-material";
import { useOrders } from "../../common";
import { OrderList, QueryContainer } from "../../components";
import { CreateOrder } from "./create-order";

const styles: Styles = {
  container: {
    display: "flex",
    flexGrow: 1,
    justifyContent: "space-between",
  },
  ordersContainer: {},
  actionsContainer: {
    display: "flex",
    padding: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    justifyContent: "flex-end",
  },
  bottomSheet: {
    position: "fixed",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "white",
    boxShadow: "0 -2px 10px rgba(0,0,0,0.1)",
  },
};

type BottomSheetProps = {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
};

const BottomSheet: React.FC<BottomSheetProps> = (props) => {
  return (
    <Modal open={props.open} onClose={props.onClose}>
      <Box sx={styles.bottomSheet}>{props.children}</Box>
    </Modal>
  );
};

const Orders: React.FC = () => {
  const { query, isSubmitting, handleToggleConfirmOrders } = useOrders();
  const [isBottomSheetOpen, setBottomSheetOpen] = useState(false);

  const handleFabClick = () => {
    setBottomSheetOpen(true);
  };

  const handleCloseBottomSheet = () => {
    setBottomSheetOpen(false);
  };

  return (
    <>
      <QueryContainer query={query} onRenderLoading={() => <></>}>
        {(data) => (
          <Stack sx={styles.container}>
            <Stack sx={styles.ordersContainer}>
              <OrderList orders={data.orders} />
            </Stack>
            <Stack sx={styles.actionsContainer}>
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
                  {data.hasConfirmedOrders
                    ? "Orders confirmed"
                    : "Confirm orders"}
                </Fab>
              )}
              {data.canCreateOrder && (
                <Fab
                  sx={styles.fab}
                  color="primary"
                  aria-label="create order"
                  onClick={handleFabClick}
                >
                  <CreateOrderIcon />
                </Fab>
              )}
            </Stack>
          </Stack>
        )}
      </QueryContainer>
      <BottomSheet open={isBottomSheetOpen} onClose={handleCloseBottomSheet}>
        <Stack spacing={2} padding={2} style={{ width: "100%" }}>
          <CreateOrder onClose={() => setBottomSheetOpen(false)} />
        </Stack>
      </BottomSheet>
    </>
  );
};

export { Orders };
