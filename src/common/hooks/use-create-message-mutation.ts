import { useGameDetailContext } from "../../context";
import { useChannelContext } from "../../context/channel-context";
import { service } from "../store";
import { useGetChannelQuery } from "./useGetChannelQuery"

const useCreateMessageMutation = () => {
    const { gameId } = useGameDetailContext();
    const { channelName } = useChannelContext();
    const getChannelQuery = useGetChannelQuery(gameId, channelName);

    const [createMessage, createMessageMutation] =
        service.endpoints.createMessage.useMutation();

    const simplifiedCreateMessage = async (body: string) => {
        if (!getChannelQuery.data) throw new Error("No channel data found");
        return createMessage({
            gameId: gameId,
            ChannelMembers: getChannelQuery.data.Members,
            Body: body,
        });
    }

    return [simplifiedCreateMessage, createMessageMutation] as const;
}

export { useCreateMessageMutation };