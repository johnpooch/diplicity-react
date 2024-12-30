import { Reducer } from "react";

type CreateOrderStatus = {
    source?: string;
    orderType?: string;
    unitType?: string;
    target?: string;
    aux?: string;
};

type CreateOrderOptions = {
    value: string;
    label: string;
    icon?: React.ReactNode;
}[];

type CreateOrderReducer = Reducer<CreateOrderState, CreateOrderAction>;

type CreateOrderState = {
    selectedOptions: string[];
    status: CreateOrderStatus;
    options: CreateOrderOptions | undefined;
}

type CreateOrderAction =
    | {
        type: "INIT";
    }
    | {
        type: "SELECT_OPTION";
        payload: string;
    }
    | {
        type: "CLICK_BACK";
    };

export type {
    CreateOrderReducer,
    CreateOrderStatus,
}
