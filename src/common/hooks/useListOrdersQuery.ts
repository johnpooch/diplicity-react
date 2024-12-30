import service from "../store/service";
import { useGetCurrentPhaseQuery } from "./useGetCurrentPhaseQuery";

const useGetOrdersQuery = (gameId: string) => {
    const { endpoints } = service;

    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);

    return endpoints.listOrders.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );
};

export { useGetOrdersQuery };