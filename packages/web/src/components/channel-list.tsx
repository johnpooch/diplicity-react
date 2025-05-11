import React from "react";
import { List, ListItem, ListItemButton, ListItemText } from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { QueryContainer } from ".";
import { service } from "../store";
import { useSelectedGameContext } from "../context";

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
};

export { ChannelList };
