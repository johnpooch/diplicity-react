import React from "react";

type Query<TData> = {
    isLoading: boolean;
    isError: boolean;
    data?: TData;
};

type QueryContainerProps<TData> = {
    query: Query<TData>;
    pending: () => React.ReactNode;
    error: () => React.ReactNode;
    fulfilled: (data: TData) => React.ReactNode;
};

const QueryContainer = <TData,>(props: QueryContainerProps<TData>) => {
    if (props.query.isLoading) {
        return <>{props.pending()}</>;
    }

    if (props.query.isError) {
        return <>{props.error()}</>;
    }

    if (props.query.data === undefined) {
        return null;
    }

    return <>{props.fulfilled(props.query.data)}</>;

};

export { QueryContainer };