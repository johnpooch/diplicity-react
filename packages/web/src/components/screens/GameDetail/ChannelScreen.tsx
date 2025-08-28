import React, { useEffect, useRef, useState } from "react";
import {
    Box,
    List,
    Stack,
    TextField,
    IconButton,
    Typography,
    Divider,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { service } from "../../../store";
import { GameDetailAppBar } from "./AppBar";
import { GameDetailLayout } from "./Layout";
import { useNavigate, useParams } from "react-router";
import { Icon, IconName } from "../../Icon";
import { createUseStyles } from "../../utils/styles";
import { Panel } from "../../Panel";
import { GameMap } from "../../GameMap";
import { ChannelMessage } from "../../ChannelMessage";

const useStyles = createUseStyles(() => ({
    root: {
        height: "100%",
        display: "flex",
        flexDirection: "column",
    },
    messagesContainer: {
        flexGrow: 1,
        padding: 1,
        minHeight: 0, // Allow container to shrink
    },
    inputContainer: {
        width: "100%",
        gap: 1,
    },
    iconButton: {
        width: 56,
    },
    emptyContainer: {
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },
}));

const ChannelScreen: React.FC = props => {
    const { gameId, channelId } = useParams<{ gameId: string; channelId: string }>();
    if (!gameId) throw new Error("Game ID is required");
    if (!channelId) throw new Error("Channel ID is required");

    const styles = useStyles(props);
    const navigate = useNavigate();
    const [message, setMessage] = useState("");

    const channelsQuery = service.endpoints.gameChannelsList.useQuery({ gameId });
    const [createMessage, createMessageMutation] = service.endpoints.gameChannelCreate2.useMutation();

    // Scroll to the bottom of the list when data is fetched
    const listRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
        }
    }, [channelsQuery.data]);

    const handleSubmit = async () => {
        const result = await createMessage({
            gameId,
            channelId: parseInt(channelId),
            channelMessageCreateRequest: {
                body: message,
            },
        });
        if (result.data) {
            setMessage("");
        }
    };

    const displayTime = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    if (channelsQuery.isError || !channelsQuery.data) {
        return null;
    }

    const channels = channelsQuery.data;
    const channel = channels.find((c) => c.id === parseInt(channelId));
    if (!channel) throw new Error("Channel not found");

    const isSubmitting = createMessageMutation.isLoading;

    return (
        <GameDetailLayout
            appBar={<GameDetailAppBar title={channel.name} onNavigateBack={() => navigate(`/game/${gameId}/chat`)} variant="secondary" />}
            rightPanel={<GameMap />}
            content={
                <Panel>
                    <Panel.Content>
                        <Stack sx={styles.root}>
                            {channel.messages.length === 0 ? (
                                <Box sx={styles.emptyContainer}>
                                    <Stack spacing={2} alignItems="center">
                                        <Icon name={IconName.Chat} sx={{ fontSize: 48, color: 'text.secondary' }} />
                                        <Typography variant="h6" color="text.secondary">
                                            No messages yet
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Start the conversation by sending a message
                                        </Typography>
                                    </Stack>
                                </Box>
                            ) : (
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
                            )}
                        </Stack>
                    </Panel.Content>
                    <Divider />
                    <Panel.Footer>
                        <Stack sx={styles.inputContainer} direction="row">
                            <TextField
                                label="Type a message"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                fullWidth
                                disabled={isSubmitting}
                            />
                            <IconButton
                                sx={styles.iconButton}
                                disabled={message === "" || isSubmitting}
                                onClick={handleSubmit}
                            >
                                <SendIcon />
                            </IconButton>
                        </Stack>
                    </Panel.Footer>
                </Panel>
            }
        />
    );
};

export { ChannelScreen };
