import { useSelectedGameContext } from "../context";
import { service } from "../store";
import { useGetSelectedChannelQuery } from "./use-get-selected-channel-query"

/**
 * Encapsulates the logic to create a message for the currently selected
 * channel, providing a simplified interface to components.
 */
const useCreateMessageMutation = () => {
    const { gameId } = useSelectedGameContext();
    const getSelectedChannelQuery = useGetSelectedChannelQuery();

    const [createMessage, createMessageMutation] =
        service.endpoints.createMessage.useMutation();

    const simplifiedCreateMessage = async (body: string) => {
        if (!getSelectedChannelQuery.data) throw new Error("No channel data found");
        return createMessage({
            gameId: gameId,
            ChannelMembers: getSelectedChannelQuery.data.Members,
            Body: body,
        });
    }

    return [simplifiedCreateMessage, createMessageMutation] as const;
}

export { useCreateMessageMutation };