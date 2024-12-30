import React from "react";
import {
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Stack,
} from "@mui/material";

import { Delete as DeleteIcon } from "@mui/icons-material";

type OrderProps = {
  source: string;
  orderType: string;
  unitTypeSvg: string;
  target?: string;
  aux?: string;
  onClickDelete?: () => void;
};

type OrdersProps =
  | {
      isLoading: true;
      orders?: undefined;
    }
  | {
      isLoading: false;
      orders: {
        nation: string;
        orders: OrderProps[];
      }[];
    };

const formatOrderText = (order: OrderProps) => {
  if (order.orderType === "Hold") {
    return `${order.source} Hold`;
  }
  if (order.orderType === "Support") {
    return `${order.source} Support ${order.target} ${order.aux}`;
  }
  return `${order.source} ${order.orderType} to ${order.target}`;
};

const Orders: React.FC<OrdersProps> = (props) => {
  if (props.isLoading) {
    return (
      <Stack spacing={2}>
        <CircularProgress />
      </Stack>
    );
  }

  return (
    <Stack spacing={2}>
      {props.orders.map(({ nation, orders }) => (
        <Stack spacing={2} key={nation}>
          <List subheader={<ListSubheader>{nation}</ListSubheader>}>
            {orders.map((order, index) => (
              <ListItem
                key={index}
                secondaryAction={
                  order.onClickDelete && (
                    <IconButton edge="end" aria-label="delete">
                      <DeleteIcon />
                    </IconButton>
                  )
                }
              >
                <ListItemIcon>
                  <img src={order.unitTypeSvg} style={{ width: 32 }} />
                </ListItemIcon>
                <ListItemText>{formatOrderText(order)}</ListItemText>
              </ListItem>
            ))}
          </List>
        </Stack>
      ))}
    </Stack>
  );
};

export { Orders };
