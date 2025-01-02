import React from "react";
import { CircularProgress, Stack, Typography } from "@mui/material";
import { useBrowseGames } from "./use-browse-games";
import { GameCard } from "../game-card";

const BrowseGames: React.FC = () => {
  const { isLoading, isError, data } = useBrowseGames();

  if (isLoading) {
    return <CircularProgress />;
  }

  if (isError) {
    return <Typography>Error</Typography>;
  }

  if (!data) throw new Error("No data");

  return (
    <Stack>
      <Typography variant="h1">Browse games</Typography>
      <Stack spacing={2} gap={2}>
        <Stack spacing={1} style={{ paddingTop: 12 }}>
          {data.map((game) => (
            <GameCard key={game.id} {...game} />
          ))}
        </Stack>
      </Stack>
    </Stack>
  );
};

export { BrowseGames };
