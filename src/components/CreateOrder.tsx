import React, { useState } from "react";
import { useFormik } from "formik";
import {
  Stack,
  Typography,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
  Select,
  Box,
  Step,
  StepLabel,
  Stepper,
} from "@mui/material";
import {
  ArrowOutward as MoveIcon,
  Shield as HoldIcon,
  CallMerge as SupportIcon,
  DirectionsBoat as ConvoyIcon,
} from "@mui/icons-material";
import service from "../common/store/service";
import { useDispatch } from "react-redux";
import { feedbackActions } from "../common/store/feedback";
import { useNavigate } from "react-router";
import { getUnit } from "@mui/material/styles/cssUtils";
import { skipToken } from "@reduxjs/toolkit/query";
import { Options } from "../common/store/service.types";
import { getOptions } from "../common/order/order";

const CreateOrder: React.FC<{
  gameId: string;
  onClickClose: () => void;
}> = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [activeStep, setActiveStep] = React.useState(0);

  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
  const getGameQuery = service.endpoints.getGame.useQuery(props.gameId);
  const variantName = getGameQuery.data?.Variant;
  const getVariantArmySvgQuery = service.endpoints.getVariantUnitSvg.useQuery(
    variantName ? { variantName: variantName, unitType: "Army" } : skipToken
  );
  const getVariantFleetSvgQuery = service.endpoints.getVariantUnitSvg.useQuery(
    variantName ? { variantName: variantName, unitType: "Fleet" } : skipToken
  );
  const listPhasesQuery = service.endpoints.listPhases.useQuery(props.gameId);
  const listPhaseStatesQuery = service.endpoints.listPhaseStates.useQuery(
    {
      gameId: props.gameId,
      phaseId: getGameQuery.data?.NewestPhaseMeta
        ? getGameQuery.data.NewestPhaseMeta[0].PhaseOrdinal.toString()
        : "",
    },
    { skip: !getGameQuery.data?.NewestPhaseMeta }
  );
  const listOptionsQuery = service.endpoints.listOptions.useQuery(
    {
      gameId: props.gameId,
      phaseId: getGameQuery.data?.NewestPhaseMeta
        ? getGameQuery.data.NewestPhaseMeta[0].PhaseOrdinal.toString()
        : "",
    },
    { skip: !getGameQuery.data?.NewestPhaseMeta }
  );

  const [createOrderMutationTrigger, createOrderQuery] =
    service.endpoints.createOrder.useMutation();

  const newestPhaseMeta = getGameQuery.data?.NewestPhaseMeta
    ? getGameQuery.data?.NewestPhaseMeta[0]
    : null;

  const newestPhase = listPhasesQuery.data?.find((phase) => {
    return phase.PhaseOrdinal === newestPhaseMeta?.PhaseOrdinal;
  });

  const variant = listVariantsQuery.data?.find((variant) => {
    return variant.Name === getGameQuery.data?.Variant;
  });

  if (!getGameQuery.isSuccess || !listPhaseStatesQuery.isSuccess) {
    return null;
  }

  if (!newestPhaseMeta) {
    throw new Error("No newest phase meta found");
  }

  const newestPhaseState = listPhaseStatesQuery.data.find((phaseState) => {
    return phaseState.PhaseOrdinal === newestPhaseMeta.PhaseOrdinal;
  });

  if (!newestPhaseState) {
    throw new Error("No newest phase state found");
  }

  const handleSelectChange = (value: string) => {
    if (selectedOptions.length === 1) {
      const source = selectedOptions[0];
      setSelectedOptions([source, value, source]);
    } else {
      setSelectedOptions((prevSelectedOptions) => {
        const newSelectedOptions = [...prevSelectedOptions, value];
        return newSelectedOptions;
      });
    }
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const onClickSave = async () => {
    // remove third element from selectedOptions
    const selectedOptionsWithoutThirdElement = selectedOptions.filter(
      (_, index) => index !== 2
    );
    try {
      await createOrderMutationTrigger({
        Parts: selectedOptionsWithoutThirdElement,
        gameId: props.gameId,
        phaseId: newestPhaseMeta.PhaseOrdinal.toString(),
      }).unwrap();
      dispatch(
        feedbackActions.setFeedback({
          message: "Order created",
          severity: "success",
        })
      );
      setSelectedOptions([]);
      props.onClickClose();
    } catch {
      dispatch(
        feedbackActions.setFeedback({
          message: "Error creating order",
          severity: "error",
        })
      );
    }
  };

  const getUnitType = (province: string) => {
    return newestPhase?.Units.find((unit) => unit.Province === province)?.Unit
      .Type as string;
  };

  const getProvinceName = (province: string) => {
    return variant?.ProvinceLongNames?.[province] || province;
  };

  const getUnitTypeSvg = (unitType: string) => {
    switch (unitType) {
      case "Army":
        return getVariantArmySvgQuery.data as string;
      case "Fleet":
        return getVariantFleetSvgQuery.data as string;
      default:
        throw new Error("Unknown unit type");
    }
  };

  const getOrderIcon = (orderType: string) => {
    switch (orderType) {
      case "Hold":
        return <HoldIcon />;
      case "Move":
        return <MoveIcon />;
      case "Support":
        return <SupportIcon />;
      case "Convoy":
        return <ConvoyIcon />;
      default:
        throw new Error("Unknown order type");
    }
  };

  console.log("selectedOptions", selectedOptions);
  console.log("activeStep", activeStep);

  const orderType = selectedOptions[1];
  const steps =
    orderType === undefined
      ? ["", "", ""]
      : ["Hold"].includes(orderType)
      ? ["", "", ""]
      : ["Move"].includes(orderType)
      ? ["", "", "", ""]
      : ["Support"].includes(orderType)
      ? ["", "", "", "", ""]
      : ["Convoy"].includes(orderType)
      ? ["", "", "", "", ""]
      : ["", "", "", "", ""];

  if (!listOptionsQuery.isSuccess) {
    return null;
  }

  const { options, type } = getOptions(listOptionsQuery.data, selectedOptions);

  console.log("options", options);
  console.log("type", type);

  return (
    <Stack spacing={2}>
      {type === "Province" ? (
        <Stack>
          {selectedOptions.length === 0 ? (
            <Typography variant="h6">Choose unit to order</Typography>
          ) : (
            <Typography variant="h6">Choose destination</Typography>
          )}
          <Stack direction={"row"}>
            {options.map((option) => (
              <Button
                key={option}
                onClick={() => handleSelectChange(option)}
                variant="contained"
              >
                <Stack>
                  {selectedOptions.length === 0 ? (
                    <div
                      dangerouslySetInnerHTML={{
                        __html: getUnitTypeSvg(getUnitType(option)),
                      }}
                    />
                  ) : null}
                  {getProvinceName(option)}
                </Stack>
              </Button>
            ))}
          </Stack>
        </Stack>
      ) : type === "OrderType" ? (
        <Stack>
          <Typography variant="h6">Choose order type</Typography>
          <Stack direction={"row"}>
            {options.map((option) => (
              <Button
                key={option}
                onClick={() => handleSelectChange(option)}
                variant="contained"
              >
                <Stack alignItems="center">
                  {getOrderIcon(option)}
                  {option}
                </Stack>
              </Button>
            ))}
          </Stack>
        </Stack>
      ) : type === undefined ? (
        <Stack>
          <Typography variant="h6">Finalize order</Typography>
          <Stack direction={"row"}>
            {selectedOptions.length === 3 ? (
              <Typography>
                {getUnitType(selectedOptions[0])} in{" "}
                {getProvinceName(selectedOptions[0])} will {selectedOptions[1]}
              </Typography>
            ) : null}
            {selectedOptions.length === 4 ? (
              <Typography>
                {getUnitType(selectedOptions[0])} in{" "}
                {getProvinceName(selectedOptions[0])} will {selectedOptions[1]}{" "}
                to {getProvinceName(selectedOptions[3])}
              </Typography>
            ) : null}
            {selectedOptions.length === 5 ? (
              <Typography>
                {getUnitType(selectedOptions[0])} in{" "}
                {getProvinceName(selectedOptions[0])} will {selectedOptions[1]}{" "}
                to {getProvinceName(selectedOptions[3])} to{" "}
                {getProvinceName(selectedOptions[4])}
              </Typography>
            ) : null}
          </Stack>
        </Stack>
      ) : null}
      <Stack direction={"row"}>
        {activeStep === 0 ? (
          <Button
            onClick={() => props.onClickClose()}
            variant="contained"
            color="error"
          >
            Cancel
          </Button>
        ) : (
          <Button
            onClick={() => {
              setSelectedOptions((prevSelectedOptions) =>
                prevSelectedOptions.slice(0, -1)
              );
              setActiveStep((prevActiveStep) => prevActiveStep - 1);
            }}
            variant="contained"
            color="error"
          >
            Back
          </Button>
        )}
        <Stepper activeStep={activeStep}>
          {steps.map((label, index) => {
            const stepProps: { completed?: boolean } = {};
            return (
              <Step key={label} {...stepProps}>
                <StepLabel />
              </Step>
            );
          })}
        </Stepper>
        <Button
          onClick={() => onClickSave()}
          variant="contained"
          color="success"
          disabled={options.length !== 0 || createOrderQuery.isLoading}
        >
          Save
        </Button>
      </Stack>
    </Stack>
  );
};

export { CreateOrder };
