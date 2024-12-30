import {
  Button,
  CircularProgress,
  FormLabel,
  Grid2,
  Skeleton,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";
import { useCreateOrder } from "./CreateOrder.hook";
import { getNumSteps, getOrderSummary } from "./CreateOrder.util";
import { CreateOrderStepIcon } from "./CreateOrder.step";
import React from "react";

const CreateOrderLoading: React.FC = () => {
  return (
    <Stack spacing={2} style={{ width: "100%" }}>
      <Skeleton variant="text" width={200} height={40} />
      <Stack justifyContent="center" direction="row">
        <CircularProgress />
      </Stack>
      <Grid2 container>
        <Button disabled>Back</Button>
        <Grid2 size="grow" alignContent="center"></Grid2>
        <Button disabled>Save</Button>
      </Grid2>
    </Stack>
  );
};

const CreateOrder: React.FC<{
  useCreateOrder?: typeof useCreateOrder;
}> = (props) => {
  const hook = props.useCreateOrder ? props.useCreateOrder : useCreateOrder;
  const {
    activeStep,
    options,
    handleSelect,
    handleBack,
    handleClose,
    handleSubmit,
    order,
    isSubmitting,
    isLoading,
    isError,
  } = hook();

  if (isLoading) return <CreateOrderLoading />;
  if (isError) return <div>Error</div>;

  return (
    <Stack spacing={2} style={{ width: "100%" }}>
      <FormLabel>Create order</FormLabel>
      <Stack justifyContent="center" direction="row">
        {order.isComplete ? (
          <Typography>{getOrderSummary(order)}</Typography>
        ) : (
          Object.entries(options).map(([key, option]) => (
            <Stack key={key} spacing={2} direction="column" alignItems="center">
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
        {!order.source && <Button onClick={handleClose}>Close</Button>}
        <Grid2 size="grow" alignContent="center">
          <Stepper activeStep={activeStep}>
            {Array.from(
              { length: getNumSteps(order.orderType?.name) },
              () => ""
            ).map((_, index) => (
              <Step key={index}>
                <StepLabel slots={{ stepIcon: CreateOrderStepIcon }} />
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
    </Stack>
  );
};

export { CreateOrder };
