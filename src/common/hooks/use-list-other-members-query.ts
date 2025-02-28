import { useSelectedGameContext } from "../context";
import { service } from "../store";
import { mergeQueries } from "./common";
import { useGetVariantQuery } from "./use-get-variant-query";

/**
 * Custom hook to list other members in the game excluding the current user.
 */
const useListOtherMembersQuery = () => {
    const { gameId } = useSelectedGameContext();
    const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
    const getGameQuery = service.endpoints.getGame.useQuery(gameId);
    const getVariantQuery = useGetVariantQuery(gameId);

    return mergeQueries(
        [getVariantQuery, getRootQuery, getGameQuery],
        (variant, user, game) => {
            return {
                members: game.Members.filter(
                    (member) => member.User.Id !== user.Id
                ).map((member) => {
                    return {
                        ...member,
                        flag: variant.Flags[member.Nation],
                    };
                }),
            };
        }
    );
};

export { useListOtherMembersQuery };
