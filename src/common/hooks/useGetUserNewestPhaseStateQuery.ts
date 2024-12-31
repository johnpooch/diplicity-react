import service from "../store/service";
import { mergeQueries } from "./common";
import { useGetCurrentPhaseQuery } from "./useGetCurrentPhaseQuery";

const useGetUserNewestPhaseStateQuery = (gameId: string) => {
    const { endpoints } = service;
    const getRootQuery = endpoints.getRoot.useQuery(undefined);
    const getGameQuery = endpoints.getGame.useQuery(gameId);
    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);
    const listPhaseStatesQuery = endpoints.listPhaseStates.useQuery(
        { gameId, phaseId: getCurrentPhaseQuery.data?.PhaseOrdinal.toString() || "" },
        { skip: !getCurrentPhaseQuery.data }
    );
    return mergeQueries([getRootQuery, getGameQuery, listPhaseStatesQuery], (user, game, phases) => {
        const userNation = game.Members.find((member) => member.User.Id === user.Id)?.Nation;
        if (!userNation) return undefined;
        const phaseState = phases.find((phase) => phase.Nation === userNation);
        return phaseState
    });
};

export { useGetUserNewestPhaseStateQuery };