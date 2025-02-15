import React from "react";
import {
  Avatar,
  Alert,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
} from "@mui/material";
import { Info as InfoIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { mergeQueries, service, useGetVariantQuery } from "../../common";
import { useParams } from "react-router";

const usePlayerInfo = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("Game ID not found");

  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const getVariantQuery = useGetVariantQuery(gameId);

  const query = mergeQueries(
    [getGameQuery, getVariantQuery],
    (game, variant) => {
      return {
        game,
        variant,
      };
    }
  );

  return { query };
};

const PlayerInfo: React.FC = () => {
  const { query } = usePlayerInfo();

  return (
    <QueryContainer query={query}>
      {(data) => (
        <>
          {!data.game.Started && (
            <Alert severity="info" icon={<InfoIcon />}>
              This game has not started yet. The game will start once{" "}
              {data.variant.Nations.length} players have joined.
            </Alert>
          )}
          <List>
            {data.game.Members.map((member) => (
              <ListItem key={member.User.Id}>
                <ListItemAvatar>
                  <Avatar src={member.User.Picture} />
                </ListItemAvatar>
                <ListItemText primary={member.User.Name} />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </QueryContainer>
  );
};

export { PlayerInfo };
