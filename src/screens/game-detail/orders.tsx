import React, { useState } from "react";
import { Stack, Fab, Modal, Box } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { useOrders } from "../../common";
import { OrderList, QueryContainer } from "../../components";
import { CreateOrder } from "./create-order";

const styles: Styles = {
  container: {
    display: "flex",
  },
  ordersContainer: {
    flex: 1,
  },
  fab: {
    position: "fixed",
    bottom: 72, // 56px for bottom navigation + 16px margin
    right: 16,
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
  const { query } = useOrders();
  const [isBottomSheetOpen, setBottomSheetOpen] = useState(false);

  const handleFabClick = () => {
    setBottomSheetOpen(true);
  };

  const handleCloseBottomSheet = () => {
    setBottomSheetOpen(false);
  };

  return (
    <Stack sx={styles.container} direction={"row"}>
      <Stack sx={styles.ordersContainer}>
        <QueryContainer query={query}>
          {(data) => <OrderList orders={data} />}
        </QueryContainer>
      </Stack>
      <Fab
        sx={styles.fab}
        color="primary"
        aria-label="create order"
        onClick={handleFabClick}
      >
        <AddIcon />
      </Fab>
      <BottomSheet open={isBottomSheetOpen} onClose={handleCloseBottomSheet}>
        <Stack spacing={2} padding={2} style={{ width: "100%" }}>
          <CreateOrder onClose={() => setBottomSheetOpen(false)} />
        </Stack>
      </BottomSheet>
    </Stack>
  );
};

export { Orders };
