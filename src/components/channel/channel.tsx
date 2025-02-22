import React, { useEffect, useRef } from "react";
import { mergeQueries, service, useGetVariantQuery } from "../../common";
import { useChannelContext } from "../../context/channel-context";
import {
  IconButton,
  List,
  ListSubheader,
  Stack,
  TextField,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { useGetUserMemberQuery } from "../../common/hooks/useGetUserMemberQuery";
import { useGetChannelQuery } from "../../common/hooks/useGetChannelQuery";
import { getChannelDisplayName } from "../../util";
import { useGameDetailContext } from "../../context";
import { ChannelMessage } from "./channel-message";

const styles: Styles = {
  listSubheader: (theme) => ({
    borderBottom: `0px solid ${theme.palette.divider}`,
    textAlign: "center",
    lineHeight: "32px",
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

const useChannel = () => {
  const { gameId } = useGameDetailContext();
  const { channelName } = useChannelContext();

  const [message, setMessage] = React.useState("");

  const [createMessage, createMessageMutation] =
    service.endpoints.createMessage.useMutation();

  const getChannelQuery = useGetChannelQuery(gameId, channelName);
  const getVariantQuery = useGetVariantQuery(gameId);
  const getUserMemberQuery = useGetUserMemberQuery(gameId);
  const listMessagesQuery = service.endpoints.listMessages.useQuery({
    gameId: gameId,
    channelId: channelName,
  });

  const isSubmitting = createMessageMutation.isLoading;

  const handleSubmit = async () => {
    const result = await createMessage({
      gameId: gameId,
      ChannelMembers: channelName.split(","),
      Body: message,
    });
    if (result.data) {
      setMessage("");
    }
  };

  const query = mergeQueries(
    [getUserMemberQuery, getVariantQuery, getChannelQuery, listMessagesQuery],
    (member, variant, channel, messages) => {
      const messagesCopy = [...messages];

      const sortedMessages = messagesCopy.sort(
        (a, b) =>
          new Date(a.CreatedAt).getTime() - new Date(b.CreatedAt).getTime()
      );

      // Group messages by the day they were created
      const groupedMessages = sortedMessages.reduce((acc, message) => {
        const date = new Date(message.CreatedAt).toLocaleDateString();
        console.log
        if (!acc[date]) {
          acc[date] = [];
        }
        acc[date].push({
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
              : variant.Flags[message.Sender], // Note, Flags isn't always defined for a variant either!
        });
        return acc;
      }, {} as Record<string, { body: string; sender: { name: string; color: string; isUser: boolean }; date: Date; flag: string }[]>);

      return {
        messages: groupedMessages,
        displayName: getChannelDisplayName(channel, variant, member),
      };
    }
  );

  const closed = channelName.includes("Diplicity");

  return { query, message, setMessage, handleSubmit, isSubmitting, closed };
};

const displayTime = (date: Date) => {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const Channel: React.FC = () => {
  const { query } = useChannel();

  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [query.data]);

  return (
    <QueryContainer query={query}>
      {(data) => (
        <Stack
          sx={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
          }}
        >
          <Stack ref={listRef} sx={{ flexGrow: 1, overflowY: "auto" }}>
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

const ChannelTextField: React.FC = () => {
  const { message, setMessage, handleSubmit, isSubmitting, closed } =
    useChannel();

  return closed ? null : (
    <Stack sx={{ gap: 1, width: "100%" }} direction="row">
      <TextField
        label="Type a message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        fullWidth
        disabled={isSubmitting}
      />
      <IconButton
        sx={{ width: 56 }}
        disabled={message === "" || isSubmitting}
        onClick={handleSubmit}
      >
        <SendIcon />
      </IconButton>
    </Stack>
  );
};

export { Channel, ChannelTextField };
