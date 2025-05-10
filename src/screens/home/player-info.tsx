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
import { service } from "../../store";
import { useSelectedGameContext } from "../../common";

const PlayerInfo: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const query = service.endpoints.gameRetrieve.useQuery({ gameId });

  return (
    <QueryContainer query={query}>
      {(game) => (
        <>
          {game.status === "pending" && (
            <Alert severity="info" icon={<InfoIcon />}>
              This game has not started yet. The game will start once{" "}
              {game.variant.nations.length} players have joined.
            </Alert>
          )}
          <List>
            {game.members.map((member) => (
              <ListItem key={member.user.username}>
                <ListItemAvatar>
                  <Avatar
                    src={member.user.profile.picture}
                    alt={member.user.username}
                  />
                </ListItemAvatar>
                <ListItemText primary={member.user.username} />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </QueryContainer>
  );
};

export { PlayerInfo };
