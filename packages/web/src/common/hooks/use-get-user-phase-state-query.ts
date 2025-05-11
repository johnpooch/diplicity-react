import service from "../store/service";
import { mergeQueries } from "./common";
import { useGetUserMemberQuery } from "./use-get-user-member-query";

/**
 * Get the phase state for the current user for a given phase.
 */
const useGetUserPhaseStateQuery = (gameId: string, phaseId: string) => {
    const { endpoints } = service;
    const getUserMemberQuery = useGetUserMemberQuery(gameId);
    const listPhaseStatesQuery = endpoints.listPhaseStates.useQuery(
        { gameId, phaseId: phaseId },
    );
    return mergeQueries([getUserMemberQuery, listPhaseStatesQuery], (userMember, phaseStates) => {
        const phaseState = phaseStates.find((phase) => phase.Nation === userMember.Nation);
        return phaseState
    });
};

export { useGetUserPhaseStateQuery };