import { skipToken } from "@reduxjs/toolkit/query";
import service from "../store/service";

const useGetMapSvgQuery = (gameId: string) => {
    const { endpoints } = service;

    const getGameQuery = endpoints.getGame.useQuery(gameId);
    const getVariantMapSvgQuery = endpoints.getVariantSvg.useQuery(
        getGameQuery.data ? getGameQuery.data.Variant : skipToken
    );

    return getVariantMapSvgQuery;
};

export { useGetMapSvgQuery };