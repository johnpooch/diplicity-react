import React from "react";
import {
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";
import { service, useGetVariantQuery, mergeQueries } from "../../common";
import { useGetUserMemberQuery } from "../../common/hooks/useGetUserMemberQuery";
import { QueryContainer } from "../../components";
import { getChannelDisplayName } from "../../util";

const styles: Styles = {
  listItemText: {
    "& .MuiListItemText-secondary": {
      overflowY: "hidden",
      textOverflow: "ellipsis",
      // whiteSpace: "nowrap",
    },
  },
  selectedListItem: (theme) => ({
    backgroundColor: theme.palette.action.selected,
  }),
};

const useChannelList = () => {
  const { gameId } = useGameDetailContext();
  const listChannelsQuery = service.endpoints.listChannels.useQuery(gameId);
  const getVariantQuery = useGetVariantQuery(gameId);
  const getUserMemberQuery = useGetUserMemberQuery(gameId);

  const query = mergeQueries(
    [getUserMemberQuery, getVariantQuery, listChannelsQuery],
    (member, variant, channels) => {
      const sortedChannels = [...channels].sort((a, b) => {
        const aDate = new Date(a.LatestMessage.CreatedAt);
        const bDate = new Date(b.LatestMessage.CreatedAt);
        return bDate.getTime() - aDate.getTime();
      });
      return sortedChannels.map((channel) => {
        return {
          name: channel.Name,
          displayName: getChannelDisplayName(channel, variant, member),
          avatar: "",
          members: channel.Members,
          messagePreview: channel.LatestMessage.Body,
        };
      });
    }
  );
  return { query };
};

const ChannelList: React.FC = () => {
  const { query } = useChannelList();
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  const location = useLocation();

  const handleChannelClick = (name: string) => {
    navigate(`/game/${gameId}/chat/channel/${name}`);
  };

  // Use regex to get the channel name from the URL
  // e.g. .../channel/Germany,Italy -> Germany,Italy
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
                <ListItemAvatar>
                  <Avatar>{channel.name.charAt(0)}</Avatar>
                </ListItemAvatar>
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

export { ChannelList };
