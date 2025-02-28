import { useSelectedChannelContext, useSelectedGameContext } from "../context";
import { service } from "../store";
import { mergeQueries } from "./common";
import { useGetUserMemberQuery } from "./use-get-user-member-query";
import { useGetVariantQuery } from "./use-get-variant-query";

/**
 * Custom hook to fetch and format messages the selected channel. Hydrates
 * messages with data from variant and user memeber queries.
 */
const useListMessagesQuery = () => {
    const { gameId } = useSelectedGameContext();
    const { channelName } = useSelectedChannelContext();

    const listMessagesQuery = service.endpoints.listMessages.useQuery({
        gameId: gameId,
        channelId: channelName,
    });
    const getVariantQuery = useGetVariantQuery(gameId);
    const getUserMemberQuery = useGetUserMemberQuery(gameId);

    return mergeQueries(
        [getUserMemberQuery, getVariantQuery, listMessagesQuery],
        (member, variant, groupedMessages) => {
            const messages = Object.keys(groupedMessages).reduce((acc, date) => {
                acc[date] = groupedMessages[date].map((message) => ({
                    body: message.Body,
                    sender: {
                        name: message.Sender,
                        color: variant.Colors[message.Sender],
                        isUser: message.Sender === member.Nation,
                    },
                    date: new Date(message.CreatedAt),
                    flag:
                        message.Sender === "Diplicity"
                            ? "/otto.png"
                            : variant.Flags[message.Sender],
                }));
                return acc as Record<string, Message[]>;
            }, {} as Record<string, Message[]>);

            return {
                messages,
            };
        }
    );
};

type Message = {
    body: string;
    sender: {
        name: string;
        color: string;
        isUser: boolean;
    };
    date: Date;
    flag: string;
};

export { useListMessagesQuery };
