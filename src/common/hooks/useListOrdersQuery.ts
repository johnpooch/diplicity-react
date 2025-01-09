import service from "../store/service";
import { useGetPhaseQuery } from "./useGetPhaseQuery";

const useGetOrdersQuery = (gameId: string, phaseId: number) => {
    const { endpoints } = service;

    const getCurrentPhaseQuery = useGetPhaseQuery(gameId, phaseId);

    return endpoints.listOrders.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );
};

export { useGetOrdersQuery };