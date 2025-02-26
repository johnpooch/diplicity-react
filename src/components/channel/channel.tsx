import React, { useEffect, useRef } from "react";
import { List, ListSubheader, Stack } from "@mui/material";
import { QueryContainer } from "../../components";
import { useListMessagesQuery } from "../../common/hooks/use-list-messages-query";
import { ChannelMessage } from "./channel-message";

/**
 * Channel component that displays a list of messages in a channel.
 */
const Channel: React.FC = () => {
  const { query } = useListMessagesQuery();

  // Scroll to the bottom of the list when data is fetched
  const listRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [query.data]);

  return (
    <QueryContainer query={query}>
      {(data) => (
        <Stack sx={styles.root}>
          <Stack ref={listRef} sx={styles.messagesContainer}>
            <List disablePadding>
              {Object.keys(data.messages).map((date) => (
                <React.Fragment key={date}>
                  <ListSubheader sx={styles.listSubheader}>
                    {date}
                  </ListSubheader>
                  <Stack p={1} spacing={1}>
                    {data.messages[date].map((message, index, messages) => {
                      const isSameSenderAsPrevious =
                        index > 0 &&
                        messages[index - 1].sender.name === message.sender.name;
                      const isNewDay =
                        index === 0 ||
                        new Date(
                          messages[index - 1].date
                        ).toLocaleDateString() !==
                          new Date(message.date).toLocaleDateString();

                      const showAvatar = !isSameSenderAsPrevious || isNewDay;

                      return (
                        <ChannelMessage
                          key={index}
                          name={message.sender.name}
                          message={message.body}
                          date={displayTime(message.date)}
                          showAvatar={showAvatar}
                          avatar={message.flag}
                          color={message.sender.color}
                          isUser={message.sender.isUser}
                        />
                      );
                    })}
                  </Stack>
                </React.Fragment>
              ))}
            </List>
          </Stack>
        </Stack>
      )}
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
