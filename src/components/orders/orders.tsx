import React from "react";
import {
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Stack,
  styled,
  Theme,
  Typography,
  useTheme,
} from "@mui/material";

import {
  CheckCircle as OrderOkIcon,
  Cancel as OrderErrorIcon,
} from "@mui/icons-material";

import { useOrders } from "./use-orders";

type OrderProps = {
  source: string;
  orderType: string;
  target?: string;
  aux?: string;
};

const StyledListItem = styled(ListItem)(({ theme }) => ({
  border: `1px solid ${theme.palette.grey[200]}`,
}));

const StyledListSubheader = styled(ListSubheader)(({ theme }) => ({
  textAlign: "left",
  fontWeight: "bold",
  border: `1px solid ${theme.palette.grey[200]}`,
  backgroundColor: theme.palette.grey[200],
}));

const formatOrderText = (order: OrderProps) => {
  if (order.orderType === "Hold") {
    return `${order.source} Hold`;
  }
  if (order.orderType === "Support") {
    return `${order.source} Support ${order.target} ${order.aux}`;
  }
  return `${order.source} ${order.orderType} to ${order.target}`;
};

const OutcomeLabelMap = {
  OK: "Succeeded",
  Bounced: "Bounced",
  SupportBroken: "Support broken",
} as const;

const OutcomeIconMap = {
  OK: (theme: Theme) => (
    <OrderOkIcon sx={{ color: theme.palette.success.main }} />
  ),
  Bounced: (theme: Theme) => (
    <OrderErrorIcon sx={{ color: theme.palette.error.main }} />
  ),
  SupportBroken: (theme: Theme) => (
    <OrderErrorIcon sx={{ color: theme.palette.error.main }} />
  ),
} as const;

const Orders: React.FC = () => {
  const theme = useTheme();
  const { isLoading, isError, orders } = useOrders();

  if (isLoading) {
    return (
      <Stack spacing={2}>
        <CircularProgress />
      </Stack>
    );
  }

  if (isError) {
    return (
      <Stack spacing={2}>
        <Typography>Error loading orders</Typography>
      </Stack>
    );
  }

  return (
    <Stack
      spacing={2}
      padding={2}
      sx={{ maxWidth: 630, width: "100%", margin: "0 auto" }}
    >
      <Typography variant="h1">Orders</Typography>
      {orders.map(({ nation, orders }) => (
        <Stack spacing={2} key={nation}>
          <List subheader={<StyledListSubheader>{nation}</StyledListSubheader>}>
            {orders.map((order, index) => (
              <StyledListItem key={index}>
                {order.outcome && (
                  <ListItemIcon>
                    {OutcomeIconMap[order.outcome](theme)}
                  </ListItemIcon>
                )}
                <Stack>
                  <ListItemText>
                    <Typography variant="h4">
                      {formatOrderText(order)}
                    </Typography>
                  </ListItemText>
                  {order.outcome && (
                    <ListItemText>
                      <Typography variant="caption">
                        {OutcomeLabelMap[order.outcome]}
                      </Typography>
                    </ListItemText>
                  )}
                </Stack>
              </StyledListItem>
            ))}
          </List>
        </Stack>
      ))}
    </Stack>
  );
};

export { Orders };
