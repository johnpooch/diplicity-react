import React from "react";
import { useGameDetailContext } from "../context";
import { mergeQueries, service, useGetVariantQuery } from "../common";
import {
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  ListItemButton,
} from "@mui/material";
import { QueryContainer } from "./query-container";
import { useNavigate } from "react-router";
import { ScreenTopBar } from "../screens/home/screen-top-bar";
import { useGetUserMemberQuery } from "../common/hooks/useGetUserMemberQuery";
import { getChannelDisplayName } from "../util";

const styles: Styles = {
  listItemText: {
    "& .MuiListItemText-secondary": {
      overflow: "hidden",
      textOverflow: "ellipsis",
      display: "block",
      whiteSpace: "nowrap",
    },
  },
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
  const navigate = useNavigate();

  const handleChannelClick = (name: string) => {
    navigate(`channel/${name}`);
  };

  return (
    <>
      <ScreenTopBar title="Conversations" />
      <QueryContainer query={query}>
        {(data) => (
          <List>
            {data.map((channel, index) => (
              <ListItem key={index} divider disablePadding>
                <ListItemButton
                  onClick={() => handleChannelClick(channel.name)}
                >
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
    </>
  );
};

export { ChannelList };
