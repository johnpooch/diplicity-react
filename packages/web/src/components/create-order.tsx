import { Stack, Typography, Button, IconButton } from "@mui/material";
import { QueryContainer } from "./query-container";
import { Close as CloseIcon } from "@mui/icons-material";
import { useCreateOrderContext, useSelectedGameContext } from "../context";
import { OrderSummary } from "./order-summary";
import { useDispatch, useSelector } from "react-redux";
import { orderSlice, Phase, service } from "../store";
import React from "react";

type Order = ReturnType<typeof orderSlice.selectors.selectOrder>;

const getStepLabel = (step: string, order: Order) => {
  if (step === "source") {
    return "Select unit to order";
  }
  if (step === "type") {
    return "Select order type";
  }
  if (step === "aux") {
    return `Select unit to ${order.type}`;
  }
  if (step === "target") {
    return "Select destination";
  }
}

const getOptions = (step: string, order: Order) => {
  if (step === "source") {
    return [{
      key: "ber",
      label: "Berlin",
    }, {
      key: "lon",
      label: "London",
    }, {
      key: "par",
      label: "Paris",
    }];
  }
  if (step === "type") {
    return [{
      key: "Hold",
      label: "Hold",
    }, {
      key: "Move",
      label: "Move",
    }, {
      key: "Support",
      label: "Support",
    }, {
      key: "Convoy",
      label: "Convoy",
    }];
  }
  if (step === "aux") {
    return [{
      key: "ber",
      label: "Berlin",
    }];
  }
  if (step === "target") {
    return [{
      key: "ber",
      label: "Berlin",
    }];
  }
  throw new Error(`Unknown step: ${step}`);
}

const getOrderSummary = (order: Order, phase: Phase) => {
  return "Berlin move to London";
}

const CreateOrderSelect: React.FC<{
  phase: Phase;
  step: string;
  order: Order;
  onSelect: (key: string) => void;
}> = (props) => {
  const label = getStepLabel(props.step, props.order);
  const options = getOptions(props.step, props.order);
  const orderSummary = getOrderSummary(props.order, props.phase);

  return (
    <Stack>
      <Typography variant="caption">
        {label}
      </Typography>
      <Typography variant="body1">{orderSummary}</Typography>
      <Stack sx={styles.optionsContainer}>
        {options.map((option) => (
          <Button key={option.key} variant="outlined" onClick={() => props.onSelect(option.key)}>{option.label}</Button>
        ))}
      </Stack>
    </Stack>
  )
}

const CreateOrderConfirm: React.FC<{
  phase: Phase;
  order: Order;
  isLoading: boolean;
  onConfirm: () => void;
}> = (props) => {
  const orderSummary = getOrderSummary(props.order, props.phase);
  return (
    <Stack>
      <Typography variant="caption">Confirm order</Typography>
      <Typography variant="body1">{orderSummary}</Typography>
      <Button onClick={props.onConfirm} disabled={props.isLoading}>Confirm</Button>
    </Stack>
  )
}

const CreateOrder: React.FC<{
  onClose: () => void;
}> = (props) => {
  const dispatch = useDispatch();
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();
  const [createOrder, { isLoading }] = service.endpoints.gameOrderCreate.useMutation();

  const order = useSelector(orderSlice.selectors.selectOrder);
  const step = useSelector(orderSlice.selectors.selectStep);
  const isComplete = useSelector(orderSlice.selectors.selectIsComplete);

  const handleSelect = (key: string) => {
    dispatch(orderSlice.actions.updateOrder(key));
  }

  const handleClose = () => {
    dispatch(orderSlice.actions.resetOrder());
    props.onClose();
  }

  const handleConfirm = async () => {
    await createOrder({
      gameId,
      orderCreateRequest: {
        source: order.source as string,
        orderType: order.type as string,
        target: order.target,
        aux: order.aux,
      },
    });
    props.onClose();
  }

  console.log("IS COMPLETE", isComplete);

  return (
    <QueryContainer query={gameRetrieveQuery}>
      {(game) => (
        <Stack sx={styles.container}>
          <Stack sx={styles.titleCloseContainer}>
            <Typography sx={{ fontWeight: "bold" }}>Create Order</Typography>
            <IconButton onClick={handleClose} disabled={isLoading}>
              <CloseIcon />
            </IconButton>
          </Stack>
          <Stack sx={styles.contentContainer}>
            {isComplete ? (
              <CreateOrderConfirm phase={game.currentPhase} order={order} isLoading={isLoading} onConfirm={handleConfirm} />
            ) : (
              <CreateOrderSelect phase={game.currentPhase} step={step} order={order} onSelect={handleSelect} />
            )}
          </Stack>
        </Stack>
      )}
    </QueryContainer>
  );
};

const styles = {
  container: {
    width: "100%",
    p: 2,
  },
  optionGroup: {
    width: "100%",
    gap: 1,
  },
  optionsContainer: {
    flexDirection: "row",
    gap: 1,
    flexWrap: "wrap",
    mt: 1,
  },
  titleCloseContainer: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexDirection: "row",
    mb: 3,
  },
  contentContainer: {
    width: "100%",
  },
} as const;

export { CreateOrder };
