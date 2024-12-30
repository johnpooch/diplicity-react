import service from "../store/service";
import { useGetCurrentPhaseQuery } from "./useGetCurrentPhaseQuery";

const useGetOptionsQuery = (gameId: string) => {
    const { endpoints } = service;

    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);

    const listOptionsQuery = endpoints.listOptions.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );

    return listOptionsQuery;
};

export { useGetOptionsQuery };