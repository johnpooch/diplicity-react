import React from "react";
import { CircularProgress, Stack, Typography } from "@mui/material";
import { useHome } from "./use-home";
import { GameCard } from "../game-card";

const Layout: React.FC<{
  children: React.ReactNode;
}> = (props) => {
  return (
    <Stack>
      <Typography variant="h1">My games</Typography>
      <Stack alignItems="center">{props.children}</Stack>
    </Stack>
  );
};

const Home: React.FC = () => {
  const { isLoading, isError, data } = useHome();

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
        {data.stagingGameCards.length > 0 && (
          <Stack>
            <Typography variant="h2">Staging Games</Typography>
            <Stack spacing={1} style={{ paddingTop: 12 }}>
              {data.stagingGameCards.map((game) => (
                <GameCard key={game.id} {...game} />
              ))}
            </Stack>
          </Stack>
        )}
        {data.startedGameCards.length > 0 && (
          <Stack>
            <Typography variant="h2">Started Games</Typography>
            <Stack spacing={1} style={{ paddingTop: 12 }}>
              {data.startedGameCards.map((game) => (
                <GameCard key={game.id} {...game} />
              ))}
            </Stack>
          </Stack>
        )}
        {data.finishedGameCards.length > 0 && (
          <Stack>
            <Typography variant="h2">Finished Games</Typography>
            <Stack spacing={1} style={{ paddingTop: 12 }}>
              {data.finishedGameCards.map((game) => (
                <GameCard key={game.id} {...game} />
              ))}
            </Stack>
          </Stack>
        )}
      </Stack>
    </Layout>
  );
};

export { Home };
