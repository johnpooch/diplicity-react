import {
  Button,
  FormLabel,
  Grid2,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";
import React from "react";
import { useCreateOrder } from "./CreateOrder.hook";
import { CreateOrderStepIcon } from "./CreateOrder.step";
import { getTitle, getOrderSummary, getNumSteps } from "./CreateOrder.util";

const CreateOrder: React.FC = () => {
  const {
    activeStep,
    onClickBack,
    onClickClose,
    onSelectOption,
    onSubmit,
    options,
    status,
  } = useCreateOrder();
  return (
    <Stack spacing={2} style={{ width: "100%" }}>
      <FormLabel>{getTitle(status)}</FormLabel>
      <Stack justifyContent="center" direction="row">
        {options ? (
          options.map((option) => (
            <Stack
              key={option.value}
              spacing={2}
              direction="column"
              alignItems="center"
            >
              {option.icon}
              <Button
                key={option.value}
                onClick={() => onSelectOption(option.value)}
              >
                {option.label}
              </Button>
            </Stack>
          ))
        ) : (
          <Typography>{getOrderSummary(status)}</Typography>
        )}
      </Stack>
      <Grid2 container>
        {onClickBack && <Button onClick={onClickBack}>Back</Button>}
        {onClickClose && <Button onClick={onClickClose}>Close</Button>}
        <Grid2 size="grow" alignContent="center">
          <Stepper activeStep={activeStep}>
            {Array.from(
              { length: getNumSteps(status.orderType) },
              () => ""
            ).map((_, index) => {
              return (
                <Step key={index}>
                  <StepLabel slots={{ stepIcon: CreateOrderStepIcon }} />
                </Step>
              );
            })}
          </Stepper>
        </Grid2>
        <Button onClick={onSubmit} disabled={Boolean(options)}>
          Save
        </Button>
      </Grid2>
    </Stack>
  );
};

export { CreateOrder };
