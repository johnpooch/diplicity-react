import service from "../store/service";
import { mergeQueries } from "./common";
import { useGetCurrentPhaseQuery } from "./use-get-current-phase-query";
import { useGetUserMemberQuery } from "./use-get-user-member-query";

/**
 * Get the newest phase state for the current user.
 */
const useGetUserNewestPhaseStateQuery = (gameId: string) => {
    const { endpoints } = service;
    const getUserMemberQuery = useGetUserMemberQuery(gameId);
    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);
    const listPhaseStatesQuery = endpoints.listPhaseStates.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );
    return mergeQueries([getUserMemberQuery, listPhaseStatesQuery], (userMember, phases) => {
        if (!userMember.Nation) return undefined;
        const phaseState = phases.find((phase) => phase.Nation === userMember.Nation);
        return phaseState
    });
};

export { useGetUserNewestPhaseStateQuery };