import service from "../store/service";
import { useGetCurrentPhaseQuery } from "./useGetCurrentPhaseQuery";

const useListNewestPhaseStatesQuery = (gameId: string) => {
    const { endpoints } = service;
    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);

    const listPhaseStatesQuery = endpoints.listPhaseStates.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );

    return listPhaseStatesQuery;
};

export { useListNewestPhaseStatesQuery };