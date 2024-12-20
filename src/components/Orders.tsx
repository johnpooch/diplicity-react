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

// listOptionsQuery.data is
// ,
// }

const Orders: React.FC<{
  gameId: string;
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

  const listOrdersQuery = service.endpoints.listOrders.useQuery(
    {
      gameId: props.gameId,
      phaseId: getGameQuery.data?.NewestPhaseMeta
        ? getGameQuery.data.NewestPhaseMeta[0].PhaseOrdinal.toString()
        : "",
    },
    { skip: !getGameQuery.data?.NewestPhaseMeta }
  );

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

  if (!listOrdersQuery.isSuccess) {
    return null;
  }

  return (
    <Stack spacing={2}>
      {listOrdersQuery.data.Orders
        ? listOrdersQuery.data.Orders.map((order) => (
            <Stack key={order.Parts[0]} spacing={2}>
              <Typography variant="h6">{order.Nation}</Typography>
              <Typography variant="body1">{order.Parts}</Typography>
            </Stack>
          ))
        : null}
    </Stack>
  );
};

export { Orders };
