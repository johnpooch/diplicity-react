import service from "../store/service";
import { mergeQueries } from "./common";

/**
 * Get the phase object for a given phase ID.
 */
const useGetPhaseQuery = (gameId: string, phaseId: number) => {
    const { endpoints } = service;

    const listPhasesQuery = endpoints.listPhases.useQuery(gameId);

    const mergedQuery = mergeQueries([listPhasesQuery], (phases) => {
        const phase = phases.find((phase) => phase.PhaseOrdinal === phaseId);
        if (!phase) throw new Error("Phase not found");
        return phase;
    });

    return mergedQuery;
};

export { useGetPhaseQuery };