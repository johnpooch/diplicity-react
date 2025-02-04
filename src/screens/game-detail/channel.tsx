import React, { useEffect, useRef } from "react";
import { ScreenTopBar } from "../home/screen-top-bar";
import { useGameDetailContext } from "../../context";
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
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { useGetUserMemberQuery } from "../../common/hooks/useGetUserMemberQuery";
import { useGetChannelQuery } from "../../common/hooks/useGetChannelQuery";
import { getChannelDisplayName } from "../../util";

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
          date: message.CreatedAt,
        });
        return acc;
      }, {} as Record<string, { body: string; sender: string; date: Date }[]>);

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

const ChannelComponent: React.FC = () => {
  const { query, message, setMessage, handleSubmit, isSubmitting, closed } =
    useChannel();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [query.data]);

  return (
    <>
      {isMobile && <ScreenTopBar title={query.data?.displayName || ""} />}
      <QueryContainer query={query}>
        {(data) => (
          <Stack
            sx={{
              display: "flex",
              flexDirection: "column",
              height: "100%",
              paddingBottom: 1,
            }}
          >
            <Stack ref={listRef} sx={{ flexGrow: 1, overflowY: "auto" }}>
              <List>
                {Object.keys(data.messages).map((date) => (
                  <React.Fragment key={date}>
                    <ListSubheader sx={styles.listSubheader}>
                      {date}
                    </ListSubheader>
                    {data.messages[date].map((message, index) => (
                      <ListItem key={index} divider>
                        <ListItemAvatar>
                          <Avatar>{message.sender[0]}</Avatar>
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
            {!closed && (
              <Stack sx={{ p: 1, gap: 1 }} direction="row">
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
            )}
          </Stack>
        )}
      </QueryContainer>
    </>
  );
};

const Channel: React.FC = () => {
  return <ChannelComponent />;
};

export { Channel };
