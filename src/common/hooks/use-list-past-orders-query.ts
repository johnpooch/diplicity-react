import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { mergeQueries } from "./common";
import { useListOrdersQuery } from "./use-list-orders-query";

/**
 * Lists the orders for a past phase.
 */
const useListPastOrdersQuery = () => {
    const { gameId } = useSelectedGameContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const ordersQuery = useListOrdersQuery(gameId, selectedPhase);

    return mergeQueries([ordersQuery], (orders) => {
        return orders;
    });
};

export { useListPastOrdersQuery };
