import { useGameDetailContext, useSelectedPhaseContext } from "../../context";
import { createMap } from "../map/map";
import { mergeQueries } from "./common";
import { useGetMapSvgQuery } from "./useGetMapSvgQuery";
import { useGetPhaseQuery } from "./useGetPhaseQuery";
import { useGetUnitSvgQuery } from "./useGetUnitSvgQuery";
import { useGetVariantQuery } from "./useGetVariantQuery";

const useMap = () => {
    const { gameId } = useGameDetailContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
    const getMapSvgQuery = useGetMapSvgQuery(gameId);
    const getArmySvgQuery = useGetUnitSvgQuery(gameId, "Army");
    const getFleetSvgQuery = useGetUnitSvgQuery(gameId, "Fleet");

    const query = mergeQueries(
        [
            getVariantQuery,
            getPhaseQuery,
            getMapSvgQuery,
            getArmySvgQuery,
            getFleetSvgQuery,
        ],
        (variant, phase, mapSvg, armySvg, fleetSvg) => {
            return createMap(mapSvg, armySvg, fleetSvg, variant, phase);
        }
    );
    return { query };
};

export { useMap };