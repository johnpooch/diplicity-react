import React from "react";
import { List, ListItem, ListItemButton, ListItemText } from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { QueryContainer } from "../../components";
import { useListChannelsQuery, useSelectedGameContext } from "../../common";

/**
 * Lists the chat channels of a game.
 */
const ChannelList: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const query = useListChannelsQuery();
  const navigate = useNavigate();
  const location = useLocation();

  const handleChannelClick = (name: string) => {
    navigate(`/game/${gameId}/chat/channel/${name}`);
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
                selectedChannel === channel.name ? styles.selectedListItem : {}
              }
            >
              <ListItemButton onClick={() => handleChannelClick(channel.name)}>
                <ListItemText
                  sx={styles.listItemText}
                  primary={channel.displayName}
                  secondary={channel.messagePreview}
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
