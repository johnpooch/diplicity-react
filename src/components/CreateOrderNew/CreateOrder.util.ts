import { useGetOptionsQuery, useGetVariantQuery } from "../../common";
import { CreateOrderInjectedProps, CreateOrderStatus } from "./CreateOrder.types";

const DEFAULT_NUM_STEPS = 3;

const NumStepsMap = new Map<string, number>([
    ["Move", 4],
    ["Support", 5],
    ["Convoy", 5],
    ["Hold", 3],
]);

const createOrderOptionTree = (
    variant: NonNullable<ReturnType<typeof useGetVariantQuery>["data"]>,
    optionTree: NonNullable<ReturnType<typeof useGetOptionsQuery>["data"]>
) => {
    const transformOptions = (innerOptions: typeof optionTree) => {
        const result = {} as CreateOrderInjectedProps["options"];

        for (const [key, value] of Object.entries(innerOptions)) {
            if (value.Type === "SrcProvince") {
                // Skip the SrcProvince layer and directly transform its children
                Object.assign(result, transformOptions(value.Next));
            } else {
                result[key] = {
                    name: variant.getProvinceLongName(key) || key,
                    children: value.Next ? transformOptions(value.Next) : {},
                };
            }
        }
        return result;
    };

    return transformOptions(optionTree);
};

const getNextOptionsNode = (optionTree: ReturnType<typeof createOrderOptionTree>, selectedOptions: string[]) => {
    let currentNode = optionTree;
    selectedOptions.forEach((option) => {
        if (currentNode) {
            currentNode = currentNode[option].children;
        }
    });
    return currentNode;
};

const getOptionAtIndex = (optionTree: ReturnType<typeof createOrderOptionTree>, selectedOptions: string[], index: number) => {
    let currentNode = optionTree;
    selectedOptions.slice(0, index).forEach((option) => {
        if (currentNode) {
            currentNode = currentNode[option].children;
        }
    });
    return currentNode ? currentNode[selectedOptions[index]] : undefined;
}

const getOrderStatus = (optionTree: ReturnType<typeof createOrderOptionTree>, selectedOptions: string[]): CreateOrderStatus => {
    const nextOptions = getNextOptionsNode(optionTree, selectedOptions);
    const sourceNode = getOptionAtIndex(optionTree, selectedOptions, 0);
    const orderTypeNode = getOptionAtIndex(optionTree, selectedOptions, 1);
    const targetNode = getOptionAtIndex(optionTree, selectedOptions, 2);
    const auxNode = getOptionAtIndex(optionTree, selectedOptions, 3);
    const isComplete = Object.keys(nextOptions).length === 0;
    return {
        source: sourceNode,
        orderType: orderTypeNode,
        target: targetNode,
        aux: auxNode,
        isComplete,
    }
}

const getNumSteps = (orderType: string | undefined) => {
    return orderType
        ? NumStepsMap.get(orderType) || DEFAULT_NUM_STEPS
        : DEFAULT_NUM_STEPS;
};

const getTitle = (status: CreateOrderStatus) => {
    if (!status.source) {
        return "Choose unit to order";
    } else if (!status.orderType) {
        return `${status.source}`;
    } else if (status.orderType.name === "Hold") {
        return `Confirm order`;
    } else if (!status.target) {
        return `${status.source} ${status.orderType.name.toLocaleLowerCase()} to`;
    } else if (status.orderType.name === "Move") {
        return `Confirm order`;
    } else if (!status.aux) {
        return `${status.source.name} ${status.orderType.name.toLocaleLowerCase()} ${status.target} to`;
    } else {
        return `Confirm order`
    }
};

const getOrderSummary = (status: CreateOrderStatus) => {
    if (status.aux) {
        return `${status.source?.name} ${status.orderType?.name?.toLocaleLowerCase()} ${status.target?.name} to ${status.aux?.name}`;
    } else if (status.target) {
        return `${status.source?.name} ${status.orderType?.name.toLocaleLowerCase()} ${status.target?.name}`;
    } else if (status.orderType) {
        return `${status.source?.name} ${status.orderType?.name?.toLocaleLowerCase()}`;
    }
};

export { getNumSteps, getTitle, getOrderSummary, createOrderOptionTree, getNextOptionsNode, getOptionAtIndex, getOrderStatus };
