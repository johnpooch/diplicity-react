import React from "react";
import { useOrderList } from "./use-order-list";
import { OrderListCurrent } from "./order-list-current";
import { OrderListPast } from "./order-list-past";
import { QueryContainer } from "../query-container";

/**
 * OrderList conditionally renders `OrderListCurrent` or `OrderListPast`
 * based on whether the selected phase is the current phase.
 */
const OrderList: React.FC = () => {
  const { query } = useOrderList();

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) =>
        data.isCurrentPhase ? <OrderListCurrent /> : <OrderListPast />
      }
    </QueryContainer>
  );
};

export { OrderList };
