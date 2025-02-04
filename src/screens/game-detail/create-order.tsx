import {
  FormLabel,
  Stack,
  Typography,
  ButtonGroup,
  Button,
  Grid2,
  Stepper,
  Step,
  StepLabel,
} from "@mui/material";
import { QueryContainer } from "../../components";
import { useCreateOrder } from "../../components/CreateOrder/CreateOrder.hook";
import { CreateOrderStepIcon } from "../../components/CreateOrder/CreateOrder.step";
import {
  getOrderSummary,
  getNumSteps,
} from "../../components/CreateOrder/CreateOrder.util";

const CreateOrder: React.FC<{
  onClose: () => void;
}> = (props) => {
  const {
    handleSelect,
    handleBack,
    handleSubmit,
    isSubmitting,
    query: createOrderQuery,
  } = useCreateOrder(props.onClose);

  return (
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
                <ButtonGroup size="large">
                  {Object.entries(options).map(([key, option]) => (
                    <Button key={key} onClick={() => handleSelect(key)}>
                      {option.name}
                    </Button>
                  ))}
                </ButtonGroup>
              )}
            </Stack>
            <Grid2 container>
              {order.source && <Button onClick={handleBack}>Back</Button>}
              {!order.source && <Button onClick={props.onClose}>Close</Button>}
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
          </>
        );
      }}
    </QueryContainer>
  );
};

export { CreateOrder };
