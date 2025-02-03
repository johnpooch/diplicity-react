import service from "../store/service";
import { mergeQueries } from "./common";

const useGetChannelQuery = (gameId: string, channelName: string) => {
    const { endpoints } = service;

    const listChannelsQuery = endpoints.listChannels.useQuery(gameId);

    const mergedQuery = mergeQueries([listChannelsQuery], (channels) => {
        const channel = channels.find((channel) => channel.Name === channelName);
        if (!channel) throw new Error("Channel not found");
        return channel;
    });

    return mergedQuery;
};

export { useGetChannelQuery };