import React from "react";
import {
    Box,
    Button,
    Chip,
    Divider,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    Stack,
    Typography,
} from "@mui/material";
import { service } from "../../store";
import { GameDetailAppBar } from "./AppBar";
import { GameDetailLayout } from "./Layout";
import { useNavigate } from "react-router";
import { Icon, IconName } from "../../components/Icon";
import { createUseStyles } from "../../components/utils/styles";
import { Panel } from "../../components/Panel-x";
import { GameMap } from "../../components/GameMap";
import { useSelectedGameContext } from "../../context";

const useStyles = createUseStyles(() => ({
    emptyContainer: {
    },
}));

const getLatestMessagePreview = (messages: any[]) => {
    if (messages.length === 0) return "No messages";
    const latestMessage = messages[messages.length - 1];
    return `${latestMessage.sender.nation.name}: ${latestMessage.body}`;
};

const ChannelListScreen: React.FC = props => {
    const { gameId } = useSelectedGameContext();

    const styles = useStyles(props);

    const query = service.endpoints.gameChannelsList.useQuery({ gameId });
    const navigate = useNavigate();

    const handleChannelClick = (id: string) => {
        navigate(`/game/${gameId}/chat/channel/${id}`);
    };

    const handleCreateChannelClick = () => {
        navigate(`/game/${gameId}/chat/channel/create`);
    };

    if (query.isError) {
        return null;
    }

    return (
        <GameDetailLayout
            appBar={<GameDetailAppBar title="Chat" onNavigateBack={() => navigate("/")} />}
            rightPanel={
                <GameMap />
            }
            content={
                <Panel>
                    <Panel.Content>
                        {query.data?.length === 0 ? (
                            <Box sx={styles.emptyContainer}>
                                <Stack spacing={2} alignItems="center">
                                    <Icon name={IconName.NoChannels} sx={{ fontSize: 48, color: 'text.secondary' }} />
                                    <Typography variant="h6" color="text.secondary">
                                        No channels created
                                    </Typography>
                                </Stack>
                            </Box>
                        ) : (
                            <List disablePadding>
                                {query.data?.map((channel, index) => (
                                    <ListItem
                                        key={index}
                                        divider
                                        disablePadding
                                    >
                                        <ListItemButton
                                            onClick={() => handleChannelClick(channel.id.toString())}
                                        >
                                            <ListItemText
                                                sx={styles.listItemText}
                                                primary={
                                                    <Stack direction="row" spacing={1} alignItems="center">
                                                        <Typography variant="body1">{channel.name}</Typography>
                                                        {!channel.private && (
                                                            <Chip
                                                                label="Public"
                                                                size="small"
                                                                variant="outlined"
                                                                sx={styles.publicChip}
                                                            />
                                                        )}
                                                    </Stack>
                                                }
                                                secondary={getLatestMessagePreview(channel.messages)}
                                            />
                                        </ListItemButton>
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Panel.Content>
                    <Divider />
                    <Panel.Footer>
                        <Button
                            variant="contained"
                            onClick={handleCreateChannelClick}
                            startIcon={<Icon name={IconName.GroupAdd} />}
                        >
                            Create Channel
                        </Button>
                    </Panel.Footer>
                </Panel>
            }
        />
    );
};

export { ChannelListScreen };


