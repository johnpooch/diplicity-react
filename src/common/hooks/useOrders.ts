import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import { mergeQueries } from "./common";
import { useGetPhaseQuery } from "./useGetPhaseQuery";
import { useGetVariantQuery } from "./useGetVariantQuery";
import { useGetOrdersQuery } from "./useListOrdersQuery";

const useOrders = () => {
    const { gameId } = useGameDetailContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
    const listOrdersQuery = useGetOrdersQuery(gameId, selectedPhase);

    const query = mergeQueries(
        [getVariantQuery, getPhaseQuery, listOrdersQuery],
        (variant, phase, orders) => {
            return orders.Orders.map((order) => {
                const [source, orderType, target, aux] = order.Parts;
                if (!source) throw new Error("No source found");
                if (!orderType) throw new Error("No orderType found");
                const outcome = phase.Resolutions?.find(
                    (resolution) => resolution.province === source
                );

                return {
                    source: variant.ProvinceLongNames[source],
                    orderType: orderType,
                    target: target ? variant.ProvinceLongNames[target] : undefined,
                    aux: aux ? variant.ProvinceLongNames[aux] : undefined,
                    nation: order.Nation,
                    outcome: outcome
                        ? {
                            outcome: outcome.outcome,
                            by: outcome.by
                                ? variant.ProvinceLongNames[outcome.by]
                                : undefined,
                        }
                        : undefined,
                };
            });
        }
    );

    return { query };
};

export { useOrders };