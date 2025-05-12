import React from "react";
import { List, ListItem, ListItemButton, ListItemText, Box, Stack, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { QueryContainer } from ".";
import { service } from "../store";
import { useSelectedGameContext } from "../context";
import { Forum as NoChannelsIcon } from "@mui/icons-material";

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

  return (
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
                      primary={channel.name}
                    // secondary={channel.messages}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </>
      )}
    </QueryContainer>
  );
};

const styles: Styles = {
  listItemText: {
    "& .MuiListItemText-secondary": {
      overflowY: "hidden",
      textOverflow: "ellipsis",
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
};

export { ChannelList };
