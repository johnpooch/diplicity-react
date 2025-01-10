import { createMap } from "../../common/map/map";
import { mergeQueries, useGetPhaseQuery, useGetMapSvgQuery, useGetUnitSvgQuery, useGetVariantQuery } from "../../common";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";

const useMap = () => {
    const { gameId } = useGameDetailContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
    const getMapSvgQuery = useGetMapSvgQuery(gameId);
    const getArmySvgQuery = useGetUnitSvgQuery(gameId, "Army");
    const getFleetSvgQuery = useGetUnitSvgQuery(gameId, "Fleet");

    return mergeQueries([getVariantQuery, getPhaseQuery, getMapSvgQuery, getArmySvgQuery, getFleetSvgQuery], (variant, phase, mapSvg, armySvg, fleetSvg) => {
        return createMap(mapSvg, armySvg, fleetSvg, variant, phase);
    });
}

export { useMap };
