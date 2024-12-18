import React from "react";
import { Stack, Typography } from "@mui/material";
import { PlayerInfoCard } from "./PlayerInfoCard";
import service from "../common/store/service";

const PlayerInfo: React.FC<{
  gameId: string;
  getGameQuery?: typeof service.endpoints.getGame.useQuery;
}> = (props) => {
  const getGameQuery = props.getGameQuery
    ? props.getGameQuery(props.gameId)
    : service.endpoints.getGame.useQuery(props.gameId);

  if (getGameQuery.isSuccess) {
    return (
      <Stack>
        <Typography variant="h1">Player Info</Typography>
        <Stack spacing={1}>
          {getGameQuery.data.Members.map((member) => (
            <PlayerInfoCard key={member.User.Id} member={member} />
          ))}
        </Stack>
      </Stack>
    );
  }
};

export { PlayerInfo };
