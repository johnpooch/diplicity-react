import { useParams } from "react-router";
import { mergeQueries, useGetVariantQuery, useGetOrdersQuery } from "../../common";
import { createOrders } from "./Orders.utils";

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
    const { gameId } = useParams<{ gameId: string }>();

    if (!gameId) throw new Error("No gameId found");

    const getVariantQuery = useGetVariantQuery(gameId);
    const listOrdersQuery = useGetOrdersQuery(gameId);

    const { isLoading, isError, data } = mergeQueries([getVariantQuery, listOrdersQuery], createOrders);

    if (isLoading) return { isLoading: true };
    if (isError) return { isError: true };
    if (!data) throw new Error("No data found");

    return {
        orders: data,
    }
};

export { useOrders };