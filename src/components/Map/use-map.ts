import { createMap } from "../../common/map/map";
import { useParams } from "react-router";
import { mergeQueries, useGetCurrentPhaseQuery, useGetMapSvgQuery, useGetUnitSvgQuery, useGetVariantQuery } from "../../common";

const useMap = () => {
    const { gameId } = useParams<{ gameId: string }>();

    if (!gameId) throw new Error("gameId is required");

    const getVariantQuery = useGetVariantQuery(gameId);
    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);
    const getMapSvgQuery = useGetMapSvgQuery(gameId);
    const getArmySvgQuery = useGetUnitSvgQuery(gameId, "Army");
    const getFleetSvgQuery = useGetUnitSvgQuery(gameId, "Fleet");

    return mergeQueries([getVariantQuery, getCurrentPhaseQuery, getMapSvgQuery, getArmySvgQuery, getFleetSvgQuery], (variant, currentPhase, mapSvg, armySvg, fleetSvg) => {
        return createMap(mapSvg, armySvg, fleetSvg, variant, currentPhase);
    });
}

export { useMap };
