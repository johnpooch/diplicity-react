import React from "react";
import { Stack, Typography } from "@mui/material";
import { usePlayerInfoQuery } from "../common/hooks/usePlayerInfo";
import { PlayerInfoCard } from "./PlayerInfoCard";

const PlayerInfo: React.FC<{
  gameId: string;
  usePlayerInfoQuery: typeof usePlayerInfoQuery;
}> = (props) => {
  const query = props.usePlayerInfoQuery(props.gameId);

  if (query.isSuccess) {
    return (
      <Stack>
        <Typography variant="h1">Player Info</Typography>
        <Stack spacing={1}>
          {query.data.users.map((user) => (
            <PlayerInfoCard key={user.id} {...user} />
          ))}
        </Stack>
      </Stack>
    );
  }
};

export { PlayerInfo };
