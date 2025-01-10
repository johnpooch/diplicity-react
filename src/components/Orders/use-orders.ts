import { mergeQueries, useGetVariantQuery, useGetOrdersQuery, useGetPhaseQuery } from "../../common";
import { createOrders } from "./orders-utils";
import { useSelectedPhaseContext } from "../selected-phase-context";
import { useGameDetailContext } from "../game-detail-context";

type LoadingState = {
    isLoading: true;
    isError?: never;
    orders?: never;
};

type ErrorState = {
    isLoading?: never;
    isError: true;
    orders?: never;
};

type SuccessState = {
    isLoading?: never;
    isError?: never;
    orders: ReturnType<typeof createOrders>;
};

const useOrders = (): LoadingState | ErrorState | SuccessState => {
    const { gameId } = useGameDetailContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
    const listOrdersQuery = useGetOrdersQuery(gameId, selectedPhase);

    const { isLoading, isError, data } = mergeQueries([getVariantQuery, getPhaseQuery, listOrdersQuery], createOrders);

    if (isLoading) return { isLoading: true };
    if (isError) return { isError: true };
    if (!data) throw new Error("No data found");

    return {
        orders: data,
    }
};

export { useOrders };