import service from "../../common/store/service";
import { getOptions, getProvinceName, getUnitType } from "../../common/utils";
import { CreateOrderReducer } from "../CreateOrder";

const createCreateOrderReducer = (
    variant: typeof service.endpoints.listVariants.Types.ResultType[number],
    game: typeof service.endpoints.getGame.Types.ResultType,
    phase: typeof service.endpoints.listPhases.Types.ResultType[number],
    optionsResponse: typeof service.endpoints.listOptions.Types.ResultType,
): CreateOrderReducer => {

    const getStatus = ([source, orderType, target, aux]: string[]) => {
        if (!source) {
            return {};
        }
        if (!orderType) {
            return {
                source: getProvinceName(variant, source),
                unitType: getUnitType(phase, source),
            };
        }
        if (!target) {
            return {
                source: getProvinceName(variant, source),
                unitType: getUnitType(phase, source),
                orderType,
            };
        }
        if (!aux) {
            return {
                source: getProvinceName(variant, source),
                unitType: getUnitType(phase, source),
                orderType,
                target: getProvinceName(variant, target),
            };
        }
        throw new Error("Invalid status");
    }

    const createOptions = (selectedOptions: string[]) => getOptions(optionsResponse, selectedOptions);

    const createDisplayOptions = (options: string[], type: string | undefined) => {
        if (!type) {
            return [];
        }
        if (type === "Province") {
            return options.map((option) => ({
                value: option,
                label: getProvinceName(variant, option),
            }));
        }
        return options.map((option) => ({
            value: option,
            label: option,
        }));
    }

    return (state, action) => {
        switch (action.type) {
            case "INIT":
                return {
                    selectedOptions: [],
                    status: {},
                    options: createDisplayOptions(createOptions([]).options, createOptions([]).type),
                };
            case "SELECT_OPTION":
                return {
                    selectedOptions: [...state.selectedOptions, action.payload],
                    status: getStatus([...state.selectedOptions, action.payload]),
                    options: createDisplayOptions(createOptions([...state.selectedOptions, action.payload]).options, createOptions([...state.selectedOptions, action.payload]).type),
                };
            case "CLICK_BACK":
                return {
                    selectedOptions: state.selectedOptions.slice(0, -1),
                    status: getStatus(state.selectedOptions.slice(0, -1)),
                    options: createDisplayOptions(createOptions(state.selectedOptions.slice(0, -1)).options, createOptions(state.selectedOptions.slice(0, -1)).type),
                };
            default:
                return state;
        };
    }
}

export { createCreateOrderReducer };