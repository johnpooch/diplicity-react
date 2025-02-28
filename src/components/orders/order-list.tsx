import React from "react";
import { OrderListCurrent } from "./order-list-current";
import { OrderListPast } from "./order-list-past";
import { QueryContainer } from "../query-container";
import {
  useGetCurrentPhaseQuery,
  useSelectedGameContext,
  useSelectedPhaseContext,
} from "../../common";

/**
 * OrderList conditionally renders `OrderListCurrent` or `OrderListPast`
 * based on whether the selected phase is the current phase.
 */
const OrderList: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const { selectedPhase } = useSelectedPhaseContext();
  const query = useGetCurrentPhaseQuery(gameId);

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) =>
        data.PhaseOrdinal === selectedPhase ? (
          <OrderListCurrent />
        ) : (
          <OrderListPast />
        )
      }
    </QueryContainer>
  );
};

export { OrderList };
