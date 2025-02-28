import { useState } from "react";
import { useCreateOrderContext } from "../context";
import { useCreateOrderMutation } from "./use-create-order-mutation";
import { mergeQueries } from "./common";
import { useListOptionsQuery } from "./use-list-options-query";

/**
 * Encapsulates the logic for creating orders and traversing the order option
 * tree.
 */
const useCreateOrder = () => {
    const { source, setSource } = useCreateOrderContext();
    if (!source) throw new Error("Source is not defined");
    const [createOrder, createOrderMutation] = useCreateOrderMutation();
    const listOptionsQuery = useListOptionsQuery();
    const [selectedOptions, setSelectedOptions] = useState([source]);

    const orderType = selectedOptions[1];

    const getLabel = (node: Node) => {
        const nodeType = Object.values(node)[0]?.Type;
        if (nodeType === "OrderType") {
            return "Select order type";
        }
        if (nodeType === "Province") {
            if (orderType === "Move" || orderType === "Retreat") {
                return "Select destination";
            }
            if (orderType === "Support" || orderType === "Convoy") {
                return selectedOptions.length === 2
                    ? `Select province to ${orderType.toLowerCase()}`
                    : "Select a destination";
            }
        }
        return "Select an option";
    };

    const query = mergeQueries([listOptionsQuery], (options) => {
        let currentNode = options[source].Next;

        const groupedOptions: GroupedOptions = [];

        selectedOptions.slice(1).forEach((step) => {
            // Convert the current node to an array of options and set selected option
            const options = Object.entries(currentNode)
                .map(createOptionFromNode)
                .map((option) => ({
                    ...option,
                    selected: step === option.key,
                }));
            // Push the transformed options to the array and define the label
            groupedOptions.push({
                label: getLabel(currentNode),
                options,
            });
            // Advance to the next node
            currentNode = currentNode[step].Next;
        });

        // If there is a next node, add it to the transformed array
        if (Object.keys(currentNode).length > 0) {
            const nextOptions = Object.entries(currentNode).map(createOptionFromNode);
            groupedOptions.push({
                label: getLabel(currentNode),
                options: nextOptions,
            });
        }

        return groupedOptions;
    });

    const handleClose = () => {
        setSource(undefined);
    };

    const handleCreateOrder = async (order: string[]) => {
        await createOrder(order);
        setSource(undefined);
    };

    const handleChange = (selectedOption: string, level: number) => {
        const options = listOptionsQuery.data;
        if (!options) throw new Error("Option is not defined");

        const newSelectedOptions = selectedOptions.slice(0, level + 1);
        newSelectedOptions.push(selectedOption);
        setSelectedOptions(newSelectedOptions);

        // Check if there is a next node
        let currentNode = options[source].Next;
        newSelectedOptions.slice(1).forEach((step) => {
            currentNode = currentNode[step].Next;
        });
        if (Object.keys(currentNode).length === 0) {
            handleCreateOrder(newSelectedOptions);
        }
    };

    const isSubmitting = createOrderMutation.isLoading;

    return {
        query,
        handleCreateOrder,
        handleClose,
        handleChange,
        isSubmitting,
    };
};

type GroupedOptions = {
    label: string;
    options: { key: string; label: string; selected?: boolean }[];
}[];

type Node = Record<string, { Name?: string; Next: Node; Type: string }>;

const createOptionFromNode = ([key, value]: [string, { Name?: string }]) => ({
    key,
    label: value.Name ? value.Name : key,
});

export { useCreateOrder };