import service from "../store/service";
import { mergeQueries } from "./common";

/**
 * Gets the current phase object for the currently selected game.
 */
const useGetCurrentPhaseQuery = (gameId: string) => {
    const { endpoints } = service;

    const listPhasesQuery = endpoints.listPhases.useQuery(gameId);
    const getGameQuery = endpoints.getGame.useQuery(gameId);

    const mergedQuery = mergeQueries([listPhasesQuery, getGameQuery], (phases, game) => {
        const phase = phases.find((phase) => phase.PhaseOrdinal === game.NewestPhaseMeta?.PhaseOrdinal);
        if (!phase) throw new Error("Phase not found");
        return phase
    });

    return mergedQuery;
};

export { useGetCurrentPhaseQuery };