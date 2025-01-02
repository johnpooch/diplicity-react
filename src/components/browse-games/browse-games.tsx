import React from "react";
import { CircularProgress, Stack, Typography } from "@mui/material";
import { useBrowseGames } from "./use-browse-games";
import { GameCard } from "../game-card";

const Layout: React.FC<{
  children: React.ReactNode;
}> = (props) => {
  return (
    <Stack>
      <Typography variant="h1">Browse games</Typography>
      <Stack alignItems="center">{props.children}</Stack>
    </Stack>
  );
};

const BrowseGames: React.FC = () => {
  const { isLoading, isError, data } = useBrowseGames();

  if (isLoading) {
    return (
      <Layout>
        <CircularProgress />
      </Layout>
    );
  }

  if (isError) {
    return <Typography>Error</Typography>;
  }

  if (!data) throw new Error("No data");

  return (
    <Layout>
      <Stack spacing={2} gap={2}>
        <Stack spacing={1} style={{ paddingTop: 12 }}>
          {data.map((game) => (
            <GameCard key={game.id} {...game} />
          ))}
        </Stack>
      </Stack>
    </Layout>
  );
};

export { BrowseGames };
