import {
  Stack,
  Typography,
  ButtonGroup,
  Button,
  Grid2,
  Stepper,
  Step,
  StepLabel,
} from "@mui/material";
import { QueryContainer } from "../";
import { useCreateOrder } from "../CreateOrder/CreateOrder.hook";
import { CreateOrderStepIcon } from "../CreateOrder/CreateOrder.step";
import {
  getOrderSummary,
  getNumSteps,
} from "../../components/CreateOrder/CreateOrder.util";
import { useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";

const CreateOrder: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  const {
    handleSelect,
    handleSubmit,
    isSubmitting,
    query: createOrderQuery,
  } = useCreateOrder(() => {
    return;
  });

  const handleSubmitAndRedirect = async () => {
    await handleSubmit();
    navigate(`/game/${gameId}/orders`);
  };

  return (
    <QueryContainer query={createOrderQuery}>
      {(data) => {
        const { options, order, activeStep } = data;
        return (
          <>
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
                onClick={handleSubmitAndRedirect}
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
