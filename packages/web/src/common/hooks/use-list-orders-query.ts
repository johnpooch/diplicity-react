import { service } from "../store";
import { mergeQueries } from "./common";
import { useGetPhaseQuery } from "./use-get-phase-query";
import { useGetVariantQuery } from "./use-get-variant-query";

/**
 * List the orders for a given phase with full names and unit types.
 */
const useListOrdersQuery = (gameId: string, phaseId: number) => {

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, phaseId);
    const listOrdersQuery = service.endpoints.listOrders.useQuery(
        { gameId, phaseId: getPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getPhaseQuery.data }
    );

    const mergedQuery = mergeQueries([getVariantQuery, getPhaseQuery, listOrdersQuery], (variant, phase, listOrders) => {
        // Orders are grouped by nation. Iterate over them and replace any province with the full name and add a unit type
        return Object.entries(listOrders.orders).reduce((acc, [nation, orders]) => {
            const ordersWithFullNames = orders.map((order) => {
                const outcome = phase.Resolutions?.find(
                    (resolution) => resolution.province === order.source
                );
                return {
                    key: order.source,
                    source: variant.ProvinceLongNames[order.source],
                    destination: order.destination ? variant.ProvinceLongNames[order.destination] : undefined,
                    aux: order.aux ? variant.ProvinceLongNames[order.aux] : undefined,
                    type: order.type,
                    unitType: phase.Units.find((unit) => unit.Province === order.source)?.Unit.Type,
                    inconsistencies: listOrders.inconsistencies[order.source],
                    outcome: outcome
                        ? {
                            outcome: outcome.outcome,
                            by: outcome.by
                                ? variant.ProvinceLongNames[outcome.by]
                                : undefined,
                        }
                        : undefined,
                }
            });
            acc[nation] = ordersWithFullNames;
            return acc;
        }, {} as Record<string, {
            key: string, source: string; destination?: string; aux?: string; type: string; unitType?: string, outcome?: {
                outcome: string;
                by?: string;
            }
        }[]>);
    });

    return mergedQuery;
};

export { useListOrdersQuery };