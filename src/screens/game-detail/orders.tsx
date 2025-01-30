import React from "react";
import { Divider, Stack } from "@mui/material";
import { useOrders } from "../../common";
import { OrderList, QueryContainer } from "../../components";
import { GameDetailAppBar } from "./app-bar";

const styles: Styles = {
  container: (theme) => ({
    display: "flex",
    border: `1px solid ${theme.palette.divider}`,
  }),
  ordersContainer: {
    flex: 1,
  },
};

const Orders: React.FC = () => {
  const { query } = useOrders();

  return (
    <Stack sx={styles.container} direction={"row"}>
      <Stack sx={styles.ordersContainer}>
        <GameDetailAppBar />
        <Divider />
        <QueryContainer query={query}>
          {(data) => <OrderList orders={data} />}
        </QueryContainer>
      </Stack>
    </Stack>
  );
};

export { Orders };
