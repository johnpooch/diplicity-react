import { skipToken } from "@reduxjs/toolkit/query";
import service from "../store/service";
import { useSelectedGameContext } from "../context";

const useGetMapSvgQuery = () => {
    const { endpoints } = service;
    const { gameId } = useSelectedGameContext();

    const getGameQuery = endpoints.getGame.useQuery(gameId);
    const getVariantMapSvgQuery = endpoints.getVariantSvg.useQuery(
        getGameQuery.data ? getGameQuery.data.Variant : skipToken
    );

    return getVariantMapSvgQuery;
};

export { useGetMapSvgQuery };