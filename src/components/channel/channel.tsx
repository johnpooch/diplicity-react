import React, { useEffect, useRef } from "react";
import { mergeQueries, service, useGetVariantQuery } from "../../common";
import { useChannelContext } from "../../context/channel-context";
import {
  Avatar,
  IconButton,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListSubheader,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { useGetUserMemberQuery } from "../../common/hooks/useGetUserMemberQuery";
import { useGetChannelQuery } from "../../common/hooks/useGetChannelQuery";
import { getChannelDisplayName } from "../../util";
import { useGameDetailContext } from "../../context";

const styles: Styles = {
  listSubheader: (theme) => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
    textAlign: "center",
  }),
  listItemText: {
    "& .MuiListItemText-primary": (theme) => ({
      color: theme.palette.text.secondary,
      fontSize: theme.typography.body2.fontSize,
    }),
    "& .MuiListItemText-secondary": (theme) => ({
      color: theme.palette.text.primary,
      fontSize: theme.typography.body1.fontSize,
    }),
  },
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
        if (!acc[date]) {
          acc[date] = [];
        }
        acc[date].push({
          body: message.Body,
          sender: message.Sender,
          date: new Date(message.CreatedAt),
          flag:
            message.Sender === "Diplicity"
              ? "/otto.png"
              : variant.Flags[message.Sender],
        });
        return acc;
      }, {} as Record<string, { body: string; sender: string; date: Date; flag: string }[]>);

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
                  {data.messages[date].map((message, index) => (
                    <ListItem key={index} divider>
                      <ListItemAvatar>
                        <Avatar src={message.flag}>{message.sender[0]}</Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        sx={styles.listItemText}
                        primary={message.sender}
                        secondary={
                          <Stack
                            direction="row"
                            justifyContent="space-between"
                            alignItems="flex-end"
                            gap={1}
                          >
                            <Typography>{message.body}</Typography>
                            <Typography sx={styles.listItemTextDate}>
                              {displayTime(new Date(message.date))}
                            </Typography>
                          </Stack>
                        }
                      />
                    </ListItem>
                  ))}
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
