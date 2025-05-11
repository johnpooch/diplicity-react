import { skipToken } from "@reduxjs/toolkit/query";
import service from "../store/service";
import { useSelectedGameContext } from "../context";

const useGetUnitSvgQuery = (unitType: string) => {
    const { endpoints } = service;
    const { gameId } = useSelectedGameContext();

    const getGameQuery = endpoints.getGame.useQuery(gameId);
    const getVariantUnitSvgQuery = endpoints.getVariantUnitSvg.useQuery(
        getGameQuery.data ? { variantName: getGameQuery.data.Variant, unitType } : skipToken
    );

    return getVariantUnitSvgQuery;
};

export { useGetUnitSvgQuery };