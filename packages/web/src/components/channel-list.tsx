import React from "react";
import { List, ListItem, ListItemButton, ListItemText, Box, Stack, Typography, Chip, Fab, Divider, Button } from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { Panel, QueryContainer } from ".";
import { service } from "../store";
import { useSelectedGameContext } from "../context";
import { Forum as NoChannelsIcon } from "@mui/icons-material";
import { GroupAdd as GroupAddIcon } from "@mui/icons-material";
import { Public as PublicIcon } from "@mui/icons-material";

/**
 * Lists the chat channels of a game.
 */
const ChannelList: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const query = service.endpoints.gameChannelsList.useQuery({ gameId });
  const navigate = useNavigate();
  const location = useLocation();

  const handleChannelClick = (id: string) => {
    navigate(`/game/${gameId}/chat/channel/${id}`);
  };

  const selectedChannel = location.pathname.match(/\/channel\/(.*)/)?.[1];

  const getLatestMessagePreview = (messages: any[]) => {
    if (messages.length === 0) return "No messages";
    const latestMessage = messages[messages.length - 1];
    return `${latestMessage.sender.nation.name}: ${latestMessage.body}`;
  };

  const handleCreateChannel = () => {
    navigate(`/game/${gameId}/chat/channel/create`);
  };

  return (
    <Panel>
      <Panel.Content>
        <QueryContainer query={query}>
          {(data) => (
            <>
              {data.length === 0 ? (
                <Box sx={styles.emptyContainer}>
                  <Stack spacing={2} alignItems="center">
                    <NoChannelsIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
                    <Typography variant="h6" color="text.secondary">
                      No channels created
                    </Typography>
                  </Stack>
                </Box>
              ) : (
                <List>
                  {data.map((channel, index) => (
                    <ListItem
                      key={index}
                      divider
                      disablePadding
                      sx={
                        selectedChannel === channel.id.toString()
                          ? styles.selectedListItem
                          : {}
                      }
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
                                  icon={<PublicIcon />}
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
            </>
          )}
        </QueryContainer>
      </Panel.Content>
      <Divider />
      <Panel.Footer>
        <Button
          variant="contained"
          onClick={handleCreateChannel}
          startIcon={<GroupAddIcon />}
        >
          Create Channel
        </Button>
      </Panel.Footer>
    </Panel>
  );
};

const styles: Styles = {
  listItemText: {
    "& .MuiListItemText-secondary": {
      overflowY: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap",
    },
  },
  selectedListItem: (theme) => ({
    backgroundColor: theme.palette.action.selected,
  }),
  emptyContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    padding: 2,
    "& .MuiTypography-root": {
      textAlign: "center",
    },
  },
  publicChip: {
    height: 24,
    "& .MuiChip-icon": {
      fontSize: 16,
    },
  },
};

export { ChannelList };
