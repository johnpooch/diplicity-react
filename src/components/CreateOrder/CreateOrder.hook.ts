import { useState } from "react";
import { mergeQueries, useCreateOrderMutation, useGetOptionsQuery, useGetVariantQuery } from "../../common";
import { createOrderOptionTree, getNextOptionsNode, getOrderStatus } from "./CreateOrder.util";
import { useGameDetailContext } from "../../context";

const useCreateOrder = (
    onOrderCreated: () => void,
) => {
    const { gameId } = useGameDetailContext();
    const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

    const getVariantQuery = useGetVariantQuery(gameId);
    const getOptionsQuery = useGetOptionsQuery(gameId);
    const [createOrder, createOrderMutation] = useCreateOrderMutation(gameId);
    const query = mergeQueries([getVariantQuery, getOptionsQuery], (variant, optionsData) => {
        const data = createOrderOptionTree(variant, optionsData);
        const options = getNextOptionsNode(data, selectedOptions);
        const order = getOrderStatus(data, selectedOptions);
        const activeStep = selectedOptions.length;
        return { options, order, activeStep };
    });

    const handleSelect = (option: string) => {
        setSelectedOptions([...selectedOptions, option]);
    };

    const handleBack = () => {
        setSelectedOptions(selectedOptions.slice(0, -1));
    }

    const handleSubmit = async () => {
        await createOrder(selectedOptions)
        onOrderCreated();
        setSelectedOptions([]);
    };

    const isSubmitting = createOrderMutation.isLoading;

    return {
        handleBack,
        handleSelect,
        handleSubmit,
        isSubmitting,
        query,
    }
};

export { useCreateOrder };