import React, { useState } from "react";
import {
  Divider,
  Stack,
  Fab,
  Modal,
  Box,
  Button,
  FormLabel,
  Grid2,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { useOrders } from "../../common";
import { OrderList, QueryContainer } from "../../components";
import { GameDetailAppBar } from "./app-bar";
import { useCreateOrder } from "../../components/CreateOrder/CreateOrder.hook";
import { CreateOrderStepIcon } from "../../components/CreateOrder/CreateOrder.step";
import {
  getOrderSummary,
  getNumSteps,
} from "../../components/CreateOrder/CreateOrder.util";

const styles: Styles = {
  container: (theme) => ({
    display: "flex",
    border: `1px solid ${theme.palette.divider}`,
  }),
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

  const {
    handleSelect,
    handleBack,
    handleSubmit,
    isSubmitting,
    query: createOrderQuery,
  } = useCreateOrder(() => setBottomSheetOpen(false));

  const handleFabClick = () => {
    setBottomSheetOpen(true);
  };

  const handleCloseBottomSheet = () => {
    setBottomSheetOpen(false);
  };

  return (
    <Stack sx={styles.container} direction={"row"}>
      <Stack sx={styles.ordersContainer}>
        <GameDetailAppBar />
        <Divider />
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
          <QueryContainer query={createOrderQuery}>
            {(data) => {
              const { options, order, activeStep } = data;
              return (
                <>
                  <FormLabel>Create order</FormLabel>
                  <Stack justifyContent="center" direction="row">
                    {order.isComplete ? (
                      <Typography>{getOrderSummary(order)}</Typography>
                    ) : (
                      Object.entries(options).map(([key, option]) => (
                        <Stack
                          key={key}
                          spacing={2}
                          direction="column"
                          alignItems="center"
                        >
                          {option.icon}
                          <Button key={key} onClick={() => handleSelect(key)}>
                            {option.name}
                          </Button>
                        </Stack>
                      ))
                    )}
                  </Stack>
                  <Grid2 container>
                    {order.source && <Button onClick={handleBack}>Back</Button>}
                    {!order.source && <Button onClick={close}>Close</Button>}
                    <Grid2 size="grow" alignContent="center">
                      <Stepper activeStep={activeStep}>
                        {Array.from(
                          { length: getNumSteps(order.orderType?.name) },
                          () => ""
                        ).map((_, index) => (
                          <Step key={index}>
                            <StepLabel
                              slots={{ stepIcon: CreateOrderStepIcon }}
                            />
                          </Step>
                        ))}
                      </Stepper>
                    </Grid2>
                    <Button
                      onClick={handleSubmit}
                      disabled={!order.isComplete || isSubmitting}
                    >
                      Save
                    </Button>
                  </Grid2>
                </>
              );
            }}
          </QueryContainer>
        </Stack>
      </BottomSheet>
    </Stack>
  );
};

export { Orders };
