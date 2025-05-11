import { BaseQueryFn, QueryActionCreatorResult, QueryDefinition, TypedUseQueryHookResult } from "@reduxjs/toolkit/query/react";

type QueryResult<TData> = TypedUseQueryHookResult<TData, unknown, BaseQueryFn>;

const isAnyLoading = (queries: QueryResult<unknown>[]) => {
    return queries.some((query) => query.isLoading);
};

const isAnyError = (queries: QueryResult<unknown>[]) => {
    return queries.some((query) => query.isError);
};

const isAllSuccess = (queries: QueryResult<unknown>[]) => {
    return queries.every((query) => query.isSuccess);
};

type Refetch<T> = () => QueryActionCreatorResult<QueryDefinition<unknown, BaseQueryFn, string, T, string>>

const mergeQueries = <TData, TQueries extends QueryResult<TData>[], TMergedData>(
    queries: [...TQueries],
    dataFn: (...args: { [K in keyof TQueries]: NonNullable<TQueries[K]['data']> }) => TMergedData
): TypedUseQueryHookResult<TMergedData, unknown, BaseQueryFn> => {
    const isLoading = isAnyLoading(queries);
    const isError = isAnyError(queries);
    const isSuccess = isAllSuccess(queries);
    const isFetching = queries.some((query) => query.isFetching);
    const isUninitialized = false as const;
    const error = queries.find((query) => query.isError)?.error;
    const status = queries[0].status;

    const refetch = (() => {
        return {}
    }) as Refetch<TMergedData>;

    if (isLoading) {
        return {
            error,
            status,
            isLoading,
            isFetching,
            isError: false,
            isSuccess: false,
            isUninitialized,
            data: undefined,
            refetch,
        };
    }

    if (isError) {
        return {
            error,
            status,
            isLoading: false,
            isFetching: false,
            isError,
            isSuccess: false,
            isUninitialized,
            data: undefined,
            refetch,
        };
    }

    if (!isSuccess) {
        return {
            error,
            status,
            isLoading: false,
            isFetching: false,
            isError: true,
            isSuccess: false,
            isUninitialized,
            data: undefined,
            refetch,
        };
    }

    const data = dataFn(...(queries.map(query => query.data) as { [K in keyof TQueries]: NonNullable<TQueries[K]['data']> }));
    return {
        error: undefined,
        status,
        isLoading: false,
        isFetching: false,
        isError: false,
        isSuccess: true,
        isUninitialized,
        data,
        currentData: data,
        fulfilledTimeStamp: Date.now(),
        refetch,
    }
};

export { mergeQueries };