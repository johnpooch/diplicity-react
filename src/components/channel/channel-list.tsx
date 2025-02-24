import React from "react";
import { List, ListItem, ListItemButton, ListItemText, ListItemAvatar, Avatar } from "@mui/material";
import { useLocation, useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";
import { service, useGetVariantQuery, mergeQueries } from "../../common";
import { useGetUserMemberQuery } from "../../common/hooks/useGetUserMemberQuery";
import { QueryContainer } from "../../components";
import { getChannelDisplayName } from "../../util";
import { ChannelAvatarGroup } from "./channel-avatar-group";

const styles: Styles = {
  listItemText: {
    margin: "0px",
    "& .MuiListItemText-secondary": {
      overflowY: "hidden",
      textOverflow: "ellipsis",
      // whiteSpace: "nowrap",

    },
  },
  selectedListItem: (theme) => ({
    backgroundColor: theme.palette.action.selected,
  }),
  listItemButton: {
    alignItems: "flex-start",
  },
  Avatar: {
    marginTop: "4px",
  },
};

const useChannelList = () => {
  const { gameId } = useGameDetailContext();
  const listChannelsQuery = service.endpoints.listChannels.useQuery(gameId);
  const getVariantQuery = useGetVariantQuery(gameId);
  const getUserMemberQuery = useGetUserMemberQuery(gameId);
  const gameDetailQuery = service.endpoints.getGame.useQuery(gameId);
  const query = mergeQueries(
    [getUserMemberQuery, getVariantQuery, listChannelsQuery, gameDetailQuery],
    (member, variant, channels, game) => {
      const sortedChannels = [...channels].sort((a, b) => {
        const aDate = new Date(a.LatestMessage.CreatedAt);
        const bDate = new Date(b.LatestMessage.CreatedAt);
        return bDate.getTime() - aDate.getTime();
      });
      return sortedChannels.map((channel) => {
        const memberNations = channel.Name.split(',')
          .map(nation => nation.trim())
          .filter(nation => nation.length > 0);

        const displayMembers = game?.Finished 
          ? memberNations 
          : memberNations.filter(nation => nation !== member?.Nation);
        
        return {
          name: channel.Name,
          displayName: displayMembers  // Use the same filtered list for display name
            .map((nation) => variant.Nations[nation] || nation)
            .join(', '),
          avatar: "",
          members: displayMembers,  // Use the same filtered list for avatars
          messagePreview: channel.LatestMessage.Body,
        };
      });
    }
  );
  return { query };
};

const truncateText = (text: string, maxLength: number) => {
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
};

const ChannelList: React.FC = () => {
  const { query } = useChannelList();
  const { gameId } = useGameDetailContext();
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
              <ListItemButton sx={styles.listItemButton} onClick={() => handleChannelClick(channel.name)}>
              <ListItemAvatar sx={styles.Avatar}>
                  <ChannelAvatarGroup displayNames={channel.members} />
                </ListItemAvatar>
                <ListItemText
                  sx={styles.listItemText}
                  primary={channel.displayName}
                  secondary={truncateText(channel.messagePreview, 90)}
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
