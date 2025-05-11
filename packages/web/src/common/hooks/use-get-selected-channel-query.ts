import { useSelectedChannelContext } from "../context";
import { mergeQueries } from "./common";
import { useListChannelsQuery } from "./use-list-channels-query";

/**
 * Gets the channel object for the currently selected channel.
 */
const useGetSelectedChannelQuery = () => {
    const { channelName } = useSelectedChannelContext();
    const listChannelsQuery = useListChannelsQuery();

    return mergeQueries(
        [listChannelsQuery],
        (channels) => {
            return channels.find((ch) => ch.name === channelName);
        }
    );
};

export { useGetSelectedChannelQuery };
