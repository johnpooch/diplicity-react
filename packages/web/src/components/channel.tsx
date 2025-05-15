import React, { useEffect, useRef } from "react";
import { List, Stack } from "@mui/material";
import { QueryContainer } from "./query-container";
import { ChannelMessage } from "./channel-message";
import { service } from "../store";
import { useSelectedChannelContext, useSelectedGameContext } from "../context";

/**
 * Channel component that displays a list of messages in a channel.
 */
const Channel: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const { channelName } = useSelectedChannelContext();
  const channelId = parseInt(channelName);
  const query = service.endpoints.gameChannelsList.useQuery({
    gameId,
  });

  // Scroll to the bottom of the list when data is fetched
  const listRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [query.data]);

  const displayTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <QueryContainer query={query}>
      {(channels) => {
        const channel = channels.find((c) => c.id === channelId);
        if (!channel) throw new Error("Channel not found");
        return (
          <Stack sx={styles.root}>
            <Stack ref={listRef} sx={styles.messagesContainer}>
              <List disablePadding>
                {channel.messages.map((message, index) => {
                  const showAvatar = index === 0 ||
                    channel.messages[index - 1].sender.nation !== message.sender.nation;

                  return (
                    <ChannelMessage
                      key={message.id}
                      name={message.sender.nation.name}
                      message={message.body}
                      date={displayTime(message.createdAt)}
                      showAvatar={showAvatar}
                      avatar={""}
                      color={message.sender.nation.color || "#a9a9a9"}
                      isUser={message.sender.isCurrentUser}
                    />
                  );
                })}
              </List>
            </Stack>
          </Stack>
        );
      }}
    </QueryContainer>
  );
};

const styles: Styles = {
  root: {
    height: "100%",
  },
  messagesContainer: {
    overflowY: "auto",
    flexGrow: 1,
    padding: 1
  },
};

export { Channel };
