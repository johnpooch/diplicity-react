import React from "react";
import service from "./store/service";
import { CreateOrder } from "../components/CreateOrderNew";

const getVariant = (listVariantsData: typeof service.endpoints.listVariants.Types.ResultType, getGameData: typeof service.endpoints.getGame.Types.ResultType) => {
    const variant = listVariantsData.find(
        (variant) => variant.Name === getGameData.Variant
    );
    if (!variant) {
        throw new Error("No variant found");
    }
    return variant;
}

const getNewestPhase = (listPhasesData: typeof service.endpoints.listPhases.Types.ResultType, getGameData: typeof service.endpoints.getGame.Types.ResultType) => {
    const phase = listPhasesData.find(
        (phase) =>
            phase.PhaseOrdinal === getGameData.NewestPhaseMeta?.PhaseOrdinal
    );
    if (!phase) {
        throw new Error("No newest phase found");
    }
    return phase;
}

const getUnitType = (phase: ReturnType<typeof getNewestPhase>, province: string) => {
    console.log(phase);
    return phase.Units.find((unit) => unit.Province === province)?.Unit
        .Type as string;
}

const getProvinceName = (variant: ReturnType<typeof getVariant>, province: string) => {
    return variant.ProvinceLongNames?.[province] || province;
}

const getOptions = (options: typeof service.endpoints.listOptions.Types.ResultType, selectedOptions: string[]): { options: string[], type: string | undefined } => {
    let currentOptions = options;
    let type: string | undefined = "Province";

    const firstOption = selectedOptions[0];
    const secondOption = selectedOptions[1];
    const remainingOptions = selectedOptions.slice(2);

    const selectedOptionsCopy = firstOption && secondOption ? [firstOption, secondOption, firstOption, ...remainingOptions] : selectedOptions;

    for (const selectedOption of selectedOptionsCopy) {
        if (!currentOptions[selectedOption]) {
            throw new Error("Invalid selected options")
        }
        if (currentOptions[selectedOption] && currentOptions[selectedOption].Next && Object.keys(currentOptions[selectedOption].Next).length > 0) {
            currentOptions = currentOptions[selectedOption].Next;
            type = Object.values(currentOptions)[0].Type;
        } else {
            currentOptions = [] as unknown as typeof service.endpoints.listOptions.Types.ResultType;
            type = undefined;
        }
    }

    return { options: Object.keys(currentOptions), type };
};

const createCreateOrderOptions = (variant: ReturnType<typeof getVariant>, phase: ReturnType<typeof getNewestPhase>, options: typeof service.endpoints.listOptions.Types.ResultType): React.ComponentProps<typeof CreateOrder>["options"] => {
    const transformOptions = (innerOptions: typeof options): React.ComponentProps<typeof CreateOrder>["options"] => {
        const result: React.ComponentProps<typeof CreateOrder>["options"] = {};

        for (const [key, value] of Object.entries(innerOptions)) {
            result[key] = {
                name: variant.getProvinceLongName(key) || key,
                children: value.Next ? transformOptions(value.Next) : undefined,
            };
        }

        return result;
    };

    return transformOptions(options);
}

export { getVariant, getNewestPhase, getUnitType, getProvinceName, getOptions, createCreateOrderOptions };