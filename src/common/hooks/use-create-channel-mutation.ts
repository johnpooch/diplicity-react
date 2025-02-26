import { useGameDetailContext } from "../../context";
import { useCreateChannelContext } from "../context/create-channel-context";
import { service } from "../store";
import { useGetUserMemberQuery } from "./useGetUserMemberQuery";

const useCreateChannelMutation = () => {
    const { gameId } = useGameDetailContext();
    const { selectedMembers } = useCreateChannelContext();
    const getUserMemberQuery = useGetUserMemberQuery(gameId);

    const [createMessage, createMessageMutation] =
        service.endpoints.createMessage.useMutation();

    const createChannel = async (body: string) => {
        if (!getUserMemberQuery.data) throw new Error("Data is not available yet");
        if (!selectedMembers.length) throw new Error("No members selected");
        return createMessage({
            gameId: gameId,
            ChannelMembers: [...selectedMembers, getUserMemberQuery.data.Nation],
            Body: body,
        });
    };

    return [createChannel, createMessageMutation] as const;
};

export { useCreateChannelMutation };
