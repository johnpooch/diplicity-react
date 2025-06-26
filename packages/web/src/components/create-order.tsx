import { Stack, Typography, Button, IconButton } from "@mui/material";
import { QueryContainer } from "./query-container";
import { Close as CloseIcon } from "@mui/icons-material";
import { useSelectedGameContext } from "../context";
import { useDispatch, useSelector } from "react-redux";
import { orderSlice, service } from "../store";
import React from "react";
import { getOptions, getOrderSummary, getStepLabel } from "../util";

const CreateOrderSelect: React.FC<{
  orderSummary: string;
  options: { key: string, label: string }[];
  label: string;
  onSelect: (key: string) => void;
}> = (props) => {

  return (
    <Stack>
      <Typography variant="caption">
        {props.label}
      </Typography>
      <Typography variant="body1">{props.orderSummary}</Typography>
      <Stack sx={styles.optionsContainer}>
        {props.options.map((option) => (
          <Button key={option.key} variant="outlined" onClick={() => props.onSelect(option.key)}>{option.label}</Button>
        ))}
      </Stack>
    </Stack>
  )
}

const CreateOrderConfirm: React.FC<{
  orderSummary: string;
  isLoading: boolean;
  onConfirm: () => void;
}> = (props) => {
  return (
    <Stack>
      <Typography variant="caption">Confirm order</Typography>
      <Typography variant="body1">{props.orderSummary}</Typography>
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

  return (
    <QueryContainer query={gameRetrieveQuery}>
      {(game) => {
        const userNation = game.members.find((m) => m.isCurrentUser)?.nation;
        if (!userNation) return null;
        const currentPhase = game.currentPhase;
        const options = currentPhase.options.find((o) => o.nation === userNation)?.options;
        if (!options) return null;
        const label = getStepLabel(step, order);
        const formattedOptions = getOptions(order, options, game.variant);
        const orderSummary = getOrderSummary(order, game.variant, currentPhase);

        return (
          <Stack sx={styles.container}>
            <Stack sx={styles.titleCloseContainer}>
              <Typography sx={{ fontWeight: "bold" }}>Create Order</Typography>
              <IconButton onClick={handleClose} disabled={isLoading}>
                <CloseIcon />
              </IconButton>
            </Stack>
            <Stack sx={styles.contentContainer}>
              {isComplete ? (
                <CreateOrderConfirm orderSummary={orderSummary} isLoading={isLoading} onConfirm={handleConfirm} />
              ) : (
                <CreateOrderSelect orderSummary={orderSummary} label={label} options={formattedOptions} onSelect={handleSelect} />
              )}
            </Stack>
          </Stack>
        )
      }
      }
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
