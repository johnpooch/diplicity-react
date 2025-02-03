import React from "react";
import {
  Avatar,
  Fab,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { Add as CreateChannelIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";
import { service, useGetVariantQuery, mergeQueries } from "../../common";
import { useGetUserMemberQuery } from "../../common/hooks/useGetUserMemberQuery";
import { QueryContainer } from "../../components";
import { getChannelDisplayName } from "../../util";
import { ScreenTopBar } from "../home/screen-top-bar";

const styles: Styles = {
  listItemText: {
    "& .MuiListItemText-secondary": {
      overflowY: "hidden",
      textOverflow: "ellipsis",
      // whiteSpace: "nowrap",
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
  const { gameId } = useGameDetailContext();
  const { query } = useChannelList();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const navigate = useNavigate();

  const handleCreateChannel = () => {
    navigate(`/game/${gameId}/chat/create-channel`);
  };

  const handleChannelClick = (name: string) => {
    navigate(`channel/${name}`);
  };

  return (
    <Stack>
      <Stack>
        {isMobile && <ScreenTopBar title="Conversations" />}
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
      </Stack>
      <Stack justifyContent={"flex-end"} direction={"row"} p={1}>
        <Fab
          sx={{}}
          color="primary"
          aria-label="create conversation"
          onClick={handleCreateChannel}
          variant="extended"
        >
          <CreateChannelIcon />
          <Typography>New conversation</Typography>
        </Fab>
      </Stack>
    </Stack>
  );
};

export { ChannelList };
