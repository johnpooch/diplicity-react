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
  Typography,
  useTheme,
} from "@mui/material";
import {
  CheckCircle as OrderOkIcon,
  Cancel as OrderErrorIcon,
} from "@mui/icons-material";
import { useOrders } from "./use-orders";
import { formatOrderText } from "../../util";

const StyledListItem = styled(ListItem)(({ theme }) => ({
  border: `1px solid ${theme.palette.grey[200]}`,
}));

const StyledListSubheader = styled(ListSubheader)(({ theme }) => ({
  textAlign: "left",
  fontWeight: "bold",
  border: `1px solid ${theme.palette.grey[200]}`,
  backgroundColor: theme.palette.grey[200],
}));

const StyledContainer = styled(Stack)(({ theme }) => ({
  maxWidth: 630,
  width: "100%",
  margin: "0 auto",
  gap: theme.spacing(2),
  padding: theme.spacing(2),
}));

const Orders: React.FC = () => {
  const theme = useTheme();
  const { isLoading, orders } = useOrders();

  if (isLoading) {
    return (
      <StyledContainer>
        <CircularProgress />
      </StyledContainer>
    );
  }

  if (!orders) return null;

  return (
    <StyledContainer>
      <Typography variant="h1">Orders</Typography>
      {orders.map(({ nation, orders }) => (
        <List
          key={nation}
          subheader={<StyledListSubheader>{nation}</StyledListSubheader>}
        >
          {orders.map((order, index) => (
            <StyledListItem key={index}>
              {order.outcome && (
                <ListItemIcon>
                  {order.outcome.outcome === "Succeeded" ? (
                    <OrderOkIcon sx={{ color: theme.palette.success.main }} />
                  ) : (
                    <OrderErrorIcon sx={{ color: theme.palette.error.main }} />
                  )}
                </ListItemIcon>
              )}
              <Stack>
                <ListItemText>
                  <Typography variant="h4">{formatOrderText(order)}</Typography>
                </ListItemText>
                {order.outcome && (
                  <ListItemText>
                    <Typography variant="caption">
                      {order.outcome.outcome}
                      {order.outcome.by ? ` by ${order.outcome.by}` : ""}
                    </Typography>
                  </ListItemText>
                )}
              </Stack>
            </StyledListItem>
          ))}
        </List>
      ))}
    </StyledContainer>
  );
};

export { Orders };
