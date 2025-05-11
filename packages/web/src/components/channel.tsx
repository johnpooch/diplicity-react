import React, { useEffect, useRef } from "react";
import { List, ListSubheader, Stack } from "@mui/material";
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

  return (
    <QueryContainer query={query}>
      {(channels) => {
        const channel = channels.find((c) => c.id === parseInt(channelName));
        if (!channel) throw new Error("Channel not found");
        return (
          <Stack sx={styles.root}>
            <Stack ref={listRef} sx={styles.messagesContainer}>
              <List disablePadding>
                {Object.keys(channel.messages).map((message) =>
                  JSON.stringify(message)
                )}
              </List>
            </Stack>
          </Stack>
        );
      }}
    </QueryContainer>
  );
};

const displayTime = (date: Date) => {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const styles: Styles = {
  root: {
    height: "100%",
  },
  messagesContainer: {
    overflowY: "auto",
    flexGrow: 1,
  },
  listSubheader: (theme) => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
    textAlign: "center",
  }),
  listItemTextDate: (theme) => ({
    fontSize: theme.typography.caption.fontSize,
    color: theme.palette.text.secondary,
  }),
  container: {
    display: "flex",
    maxWidth: 1000,
    width: "100%",
  },
  channelListContainer: {
    flex: 1,
  },
  channelContainer: {
    flex: 2,
  },
};

export { Channel };
