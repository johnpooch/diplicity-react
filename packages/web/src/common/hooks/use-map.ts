import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { createMap } from "../map/map";
import { mergeQueries } from "./common";
import { useGetMapSvgQuery } from "./use-get-map-svg-query";
import { useGetPhaseQuery } from "./use-get-phase-query";
import { useGetUnitSvgQuery } from "./use-get-unit-svg-query";
import { useGetVariantQuery } from "./use-get-variant-query";

const useMap = () => {
    const { gameId } = useSelectedGameContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const getVariantQuery = useGetVariantQuery(gameId);
    const getPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);
    const getMapSvgQuery = useGetMapSvgQuery();
    const getArmySvgQuery = useGetUnitSvgQuery("Army");
    const getFleetSvgQuery = useGetUnitSvgQuery("Fleet");

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