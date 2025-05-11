import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { mergeQueries } from "./common";
import { useGetUserMemberQuery } from "./use-get-user-member-query";
import { useListMissingOrdersQuery } from "./use-list-missing-orders-query";
import { useListOrdersQuery } from "./use-list-orders-query";

/**
 * Lists the orders and missing orders for the current phase and user's nation.
 */
const useListCurrentOrdersQuery = () => {
    const { gameId } = useSelectedGameContext();
    const { selectedPhase } = useSelectedPhaseContext();
    const getUserMemberQuery = useGetUserMemberQuery(gameId);
    const listHydratedOrdersQuery = useListOrdersQuery(
        gameId,
        selectedPhase
    );
    const listHydratedMissingOrdersQuery = useListMissingOrdersQuery(
        gameId,
        selectedPhase
    );

    return mergeQueries(
        [
            listHydratedOrdersQuery,
            listHydratedMissingOrdersQuery,
            getUserMemberQuery,
        ],
        (orders, missingOrders, userMember) => {
            return {
                orders: orders[userMember.Nation] ? orders[userMember.Nation] : [],
                missingOrders,
            };
        }
    );
}

export { useListCurrentOrdersQuery };