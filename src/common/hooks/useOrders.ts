import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import { mergeQueries } from "./common";
import { useGetPhaseQuery } from "./useGetPhaseQuery";
import { useGetUserPhaseStateQuery } from "./useGetUserPhaseStateQuery";
import { useGetVariantQuery } from "./useGetVariantQuery";
import { useGetOrdersQuery } from "./useListOrdersQuery";
import { useUpdatePhaseStateMutation } from "./useUpdatePhaseStateMutation";

const useOrders = () => {
    const { gameId } = useGameDetailContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const [updatePhaseStateTrigger, updatePhaseStateMutation] =
        useUpdatePhaseStateMutation(gameId);

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
    const listOrdersQuery = useGetOrdersQuery(gameId, selectedPhase);
    const getUserPhaseStateQuery = useGetUserPhaseStateQuery(gameId, selectedPhase.toString());

    const handleToggleConfirmOrders = () => {
        if (!getUserPhaseStateQuery.data) return;
        updatePhaseStateTrigger({
            isConfirmed: !getUserPhaseStateQuery.data.ReadyToResolve,
        });
    }

    const query = mergeQueries(
        [getVariantQuery, getPhaseQuery, listOrdersQuery, getUserPhaseStateQuery],
        (variant, phase, orders, phaseState) => {
            const transformedOrders = orders.Orders.map((order) => {
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
            return {
                orders: transformedOrders,
                canCreateOrder: phase.canCreateOrder,
                canConfirmOrders: phaseState.canUpdate,
                hasConfirmedOrders: phaseState.ReadyToResolve,
            }
        }
    );

    return { query, handleToggleConfirmOrders, isSubmitting: updatePhaseStateMutation.isLoading };
};

export { useOrders };