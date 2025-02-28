import { mergeQueries } from "./common";
import { useGetPhaseQuery } from "./use-get-phase-query";
import { useGetVariantQuery } from "./use-get-variant-query";
import { useGetOrdersQuery } from "./useListOrdersQuery";

/**
 * List the missing orders for a given phase.
 */
const useListMissingOrdersQuery = (gameId: string, phaseId: number) => {
    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, phaseId);
    const listOrdersQuery = useGetOrdersQuery(gameId, phaseId);

    const mergedQuery = mergeQueries([getVariantQuery, getPhaseQuery, listOrdersQuery], (variant, phase, listOrders) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        return Object.entries(listOrders.inconsistencies).filter(([_, inconsistencies]) => inconsistencies.includes("InconsistencyMissingOrder")).map(([province]) => ({
            key: province,
            source: variant.ProvinceLongNames[province],
            unitType: phase.Units.find((unit) => unit.Province === province)?.Unit.Type,
        }));
    });

    return mergedQuery;
};

export { useListMissingOrdersQuery };