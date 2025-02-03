import service from "../store/service";
import { mergeQueries } from "./common";

const useGetVariantQuery = (gameId: string) => {
    const { endpoints } = service;

    const listVariantsQuery = endpoints.listVariants.useQuery(undefined);
    const getGameQuery = endpoints.getGame.useQuery(gameId);

    const mergedQuery = mergeQueries([listVariantsQuery, getGameQuery], (variants, game) => {
        const variant = variants.find((variant) => variant.Name === game.Variant);
        if (!variant) throw new Error("Variant not found");
        return variant;
    });

    return mergedQuery;
};

export { useGetVariantQuery };