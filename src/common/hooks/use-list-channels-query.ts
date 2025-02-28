import { service, useGetVariantQuery, mergeQueries, useSelectedGameContext } from "../../common";
import { useGetUserMemberQuery } from "./use-get-user-member-query";

/**
 * Lists channels of the currently selected game.
 * 
 * Performs multiple queries and merges the results.
 */
const useListChannelsQuery = () => {
    const { gameId } = useSelectedGameContext();
    const listChannelsQuery = service.endpoints.listChannels.useQuery(gameId);
    const getVariantQuery = useGetVariantQuery(gameId);
    const getUserMemberQuery = useGetUserMemberQuery(gameId);

    return mergeQueries(
        [getUserMemberQuery, getVariantQuery, listChannelsQuery],
        (member, variant, channels) => {

            const getChannelDisplayName = (channel: typeof channels[number]) => {
                const sortedVariantNations = [...variant.Nations].sort().join(",");
                const sortedChannelMembers = [...channel.Members].sort().join(",");

                const isPublicPress = sortedVariantNations === sortedChannelMembers;

                if (isPublicPress) return "Public Press";

                const removeNation = (name: string, nation: string) => {
                    return name
                        .replace(nation, "")
                        .replace(/,,/, ",")
                        .replace(/^,/, "")
                        .replace(/,$/, "");
                };

                let displayName = channel.Name;
                if (member) {
                    displayName = removeNation(channel.Name, member.Nation);
                }

                displayName = displayName.replace(/,/g, ", ");
                return displayName;
            };

            return channels.map((channel) => {
                return {
                    ...channel,
                    name: channel.Name,
                    displayName: getChannelDisplayName(channel),
                    avatar: "",
                    members: channel.Members,
                    messagePreview: channel.LatestMessage.Body,
                };
            });
        }
    );
};

export { useListChannelsQuery };
