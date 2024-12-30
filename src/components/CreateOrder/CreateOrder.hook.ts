import { useReducer } from "react";
import { CreateOrderReducer } from "./CreateOrder.types";
import { useGameProvider } from "../GameProvider";

const emptyState: ReturnType<CreateOrderReducer> = {
    selectedOptions: [],
    status: {},
    options: undefined,
};

const useCreateOrder = () => {
    const { createOrderReducer, onCloseCreateOrder, onSubmitCreateOrder } = useGameProvider();
    const [{ selectedOptions, status, options }, dispatch] = useReducer(createOrderReducer, emptyState, (state) => createOrderReducer(state, { type: "INIT" }));

    const onSelectOption = (option: string) => {
        dispatch({ type: "SELECT_OPTION", payload: option });
    };

    const onClickBack =
        Boolean(selectedOptions.length) && (() => dispatch({ type: "CLICK_BACK" }));

    const onClickClose = !selectedOptions.length && onCloseCreateOrder;

    const onSubmit = () => {
        onSubmitCreateOrder(selectedOptions);
    };

    const activeStep = selectedOptions.length;

    return {
        activeStep,
        onClickBack,
        onClickClose,
        onSelectOption,
        onSubmit,
        options,
        status,
    };
};

export { useCreateOrder };