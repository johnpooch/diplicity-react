import service from "../store/service";
import { useGetCurrentPhaseQuery } from "./use-get-current-phase-query";
import { useGetVariantQuery } from "./use-get-variant-query";
import { mergeQueries } from "./common";
import { useSelectedGameContext } from "../context";

const useListOptionsQuery = () => {
    const { endpoints } = service;
    const { gameId } = useSelectedGameContext();
    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);
    const getVariantQuery = useGetVariantQuery(gameId);

    const listOptionsQuery = endpoints.listOptions.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );

    const mergedQuery = mergeQueries([getVariantQuery, listOptionsQuery], (variant, options) => {
        const transformOptions = (innerOptions: typeof options) => {
            const transformedOptions = {} as Record<string, typeof options[string]>;

            Object.entries(innerOptions).forEach(([key, value]) => {
                if (value.Type === "Province") {
                    const longName = variant.ProvinceLongNames[key];
                    transformedOptions[key] = {
                        ...value,
                        Name: longName,
                        Next: transformOptions(value.Next)
                    };
                } else {
                    transformedOptions[key] = {
                        ...value,
                        Next: transformOptions(value.Next)
                    };
                }
            });

            return transformedOptions;
        };

        return transformOptions(options);
    });

    return mergedQuery;
};

export { useListOptionsQuery };