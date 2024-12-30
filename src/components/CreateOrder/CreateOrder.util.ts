import { CreateOrderStatus } from "./CreateOrder.types";

const DEFAULT_NUM_STEPS = 3;

const NumStepsMap = new Map<string, number>([
    ["Move", 4],
    ["Support", 5],
    ["Convoy", 5],
    ["Hold", 3],
]);

const getNumSteps = (orderType: string | undefined) => {
    return orderType
        ? NumStepsMap.get(orderType) || DEFAULT_NUM_STEPS
        : DEFAULT_NUM_STEPS;
};

const getTitle = (status: CreateOrderStatus) => {
    if (!status.source) {
        return "Choose unit to order";
    } else if (!status.orderType) {
        return `${status.unitType} ${status.source}`;
    } else if (status.orderType === "Hold") {
        return `Confirm order`;
    } else if (!status.target) {
        return `${status.unitType} ${status.source} ${status.orderType.toLocaleLowerCase()} to`;
    } else if (status.orderType === "Move") {
        return `Confirm order`;
    } else if (!status.aux) {
        return `${status.unitType} ${status.source} ${status.orderType.toLocaleLowerCase()} ${status.target} to`;
    } else {
        return `Confirm order`
    }
};

const getOrderSummary = (status: CreateOrderStatus) => {
    if (status.aux) {
        return `${status.unitType} ${status.source} ${status.orderType?.toLocaleLowerCase()} ${status.target} to ${status.aux}`;
    } else if (status.target) {
        return `${status.unitType} ${status.source} ${status.orderType?.toLocaleLowerCase()} ${status.target}`;
    } else if (status.orderType) {
        return `${status.unitType} ${status.source} ${status.orderType?.toLocaleLowerCase()}`;
    }
};

export { getNumSteps, getTitle, getOrderSummary };
