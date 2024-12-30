import { useState } from "react";
import { mergeQueries, useCreateOrderMutation, useGetOptionsQuery, useGetVariantQuery } from "../../common";
import { useParams } from "react-router";
import { createOrderOptionTree, getNextOptionsNode, getOrderStatus } from "./CreateOrder.util";

type LoadingState = {
    isLoading: true;
    isError?: never;
    activeStep?: never;
    handleBack?: never;
    handleClose?: never;
    handleSelect?: never;
    handleSubmit?: never;
    isSubmitting?: never;
    options?: never;
    order?: never;
};

type ErrorState = {
    isLoading?: never;
    isError: true;
    activeStep?: never;
    handleBack?: never;
    handleClose?: never;
    handleSelect?: never;
    handleSubmit?: never;
    isSubmitting?: never;
    options?: never;
    order?: never;
};

type SuccessState = {
    isLoading?: never;
    isError?: never;
    activeStep: number;
    handleBack: () => void;
    handleClose: () => void;
    handleSelect: (option: string) => void;
    handleSubmit: () => void;
    isSubmitting: boolean;
    options: ReturnType<typeof getNextOptionsNode>;
    order: ReturnType<typeof getOrderStatus>;
};

const useCreateOrder = (): LoadingState | ErrorState | SuccessState => {
    const { gameId } = useParams<{ gameId: string }>();
    const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

    if (!gameId) throw new Error("No gameId found");

    const getVariantQuery = useGetVariantQuery(gameId);
    const getOptionsQuery = useGetOptionsQuery(gameId);
    const [createOrder, createOrderMutation] = useCreateOrderMutation(gameId);
    const { isLoading, isError, data } = mergeQueries([getVariantQuery, getOptionsQuery], createOrderOptionTree);

    if (isLoading) return { isLoading: true };
    if (isError) return { isError: true };

    if (!data) throw new Error("No data found");

    const handleSelect = (option: string) => {
        setSelectedOptions([...selectedOptions, option]);
    };

    const handleBack = () => {
        setSelectedOptions(selectedOptions.slice(0, -1));
    }

    const handleClose = () => {
        return
    };

    const handleSubmit = () => createOrder(selectedOptions);

    const options = getNextOptionsNode(data, selectedOptions);
    const order = getOrderStatus(data, selectedOptions);
    const activeStep = selectedOptions.length;
    const isSubmitting = createOrderMutation.isLoading;

    return {
        activeStep,
        handleBack,
        handleClose,
        handleSelect,
        handleSubmit,
        isSubmitting,
        options,
        order,
    }
};

export { useCreateOrder };