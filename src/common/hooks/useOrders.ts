import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { mergeQueries } from "./common";
import { useGetPhaseQuery } from "./use-get-phase-query";
import { useGetUserPhaseStateQuery } from "./use-get-user-phase-state-query";
import { useGetVariantQuery } from "./use-get-variant-query";
import { useGetOrdersQuery } from "./useListOrdersQuery";
import { useUpdatePhaseStateMutation } from "./useUpdatePhaseStateMutation";

const useOrders = () => {
    const { gameId } = useSelectedGameContext();
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
        (_variant, phase, _orders, phaseState) => {
            return {
                canCreateOrder: phase.canCreateOrder,
                canConfirmOrders: phaseState.canUpdate,
                hasConfirmedOrders: phaseState.ReadyToResolve,
            }
        }
    );

    return { query, handleToggleConfirmOrders, isSubmitting: updatePhaseStateMutation.isLoading };
};

export { useOrders };