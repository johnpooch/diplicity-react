import service from "../store/service";
import { mergeQueries } from "./common";

/**
 * Get the game member object for the current user.
 */
const useGetUserMemberQuery = (gameId: string) => {
    const { endpoints } = service;

    const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
    const getGameQuery = endpoints.getGame.useQuery(gameId);

    return mergeQueries([getRootQuery, getGameQuery], (user, game) => {
        return game.Members.find((member) => member.User.Id === user.Id);
    });
};

export { useGetUserMemberQuery };