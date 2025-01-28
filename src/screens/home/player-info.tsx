import React from "react";
import {
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
} from "@mui/material";
import { QueryContainer } from "../../components";
import { service } from "../../common";
import { ScreenTopBar } from "./screen-top-bar";
import { useParams } from "react-router";

const usePlayerInfo = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("Game ID not found");

  const query = service.endpoints.getGame.useQuery(gameId);

  return { query };
};

const PlayerInfo: React.FC = () => {
  const { query } = usePlayerInfo();

  return (
    <>
      <ScreenTopBar title="Player info" />
      <QueryContainer query={query}>
        {(data) => (
          <List>
            {data.Members.map((member) => (
              <ListItem key={member.User.Id}>
                <ListItemAvatar>
                  <Avatar src={member.User.Picture} />
                </ListItemAvatar>
                <ListItemText primary={member.User.Name} />
              </ListItem>
            ))}
          </List>
        )}
      </QueryContainer>
    </>
  );
};

export { PlayerInfo };
