import service from "../store/service";
import { mergeQueries } from "./common";

const useGetUserMemberQuery = (gameId: string) => {
    const { endpoints } = service;

    const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
    const getGameQuery = endpoints.getGame.useQuery(gameId);

    const mergedQuery = mergeQueries([getRootQuery, getGameQuery], (user, game) => {
        return game.Members.find((member) => member.User.Id === user.Id);
    });

    return mergedQuery;
};

export { useGetUserMemberQuery };