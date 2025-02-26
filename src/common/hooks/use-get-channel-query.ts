import { useChannelContext } from "../../context/channel-context";
import { useListChannelsQuery } from "./use-list-channels-query";
import { mergeQueries } from "../../common";

const useGetChannelQuery = () => {
    const { channelName } = useChannelContext();
    const { query: listChannelsQuery } = useListChannelsQuery();

    const query = mergeQueries(
        [listChannelsQuery],
        (channels) => {
            return channels.find((ch) => ch.name === channelName);
        }
    );

    return { query };
};

export { useGetChannelQuery };
