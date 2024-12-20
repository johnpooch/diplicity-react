import React from "react";
import { Stack, Typography } from "@mui/material";
import { GameCard, GameCallbacks } from "../components/GameCard";
import NavigationWrapper from "../components/NavigationWrapper";
import PageWrapper from "../components/PageWrapper";
import service from "../common/store/service";
import GameCardSkeleton from "../components/GameCardSkeleton";

const HomeScreen: React.FC<{
  gameCallbacks: GameCallbacks;
}> = (props) => {
  const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
  const listStagingGamesQuery = service.endpoints.listGames.useQuery(
    {
      my: true,
      status: "Staging",
      mastered: false,
    },
    { refetchOnMountOrArgChange: true }
  );
  const listStartedGamesQuery = service.endpoints.listGames.useQuery({
    my: true,
    status: "Started",
    mastered: false,
  });
  const listFinishedGamesQuery = service.endpoints.listGames.useQuery({
    my: true,
    status: "Finished",
    mastered: false,
  });

  if (!getRootQuery.isSuccess) {
    return null;
  }

  return (
    <NavigationWrapper>
      <PageWrapper>
        <Stack>
          <Typography variant="h1">My games</Typography>
          <Stack spacing={2}>
            {listStagingGamesQuery.isLoading ? (
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Staging Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  <GameCardSkeleton />
                </Stack>
              </div>
            ) : listStagingGamesQuery.isError ? (
              <Typography variant="h2">Error</Typography>
            ) : listStagingGamesQuery.isSuccess ? (
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Staging Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  {listStagingGamesQuery.data.map((game) => (
                    <GameCard
                      key={game.ID}
                      game={game}
                      user={getRootQuery.data}
                      {...props.gameCallbacks}
                    />
                  ))}
                </Stack>
              </div>
            ) : null}
            {listStartedGamesQuery.isLoading ? (
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Started Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  <GameCardSkeleton />
                </Stack>
              </div>
            ) : listStartedGamesQuery.isError ? (
              <Typography variant="h2">Error</Typography>
            ) : listStartedGamesQuery.isSuccess ? (
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Started Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  {listStartedGamesQuery.data.map((game) => (
                    <GameCard
                      key={game.ID}
                      game={game}
                      user={getRootQuery.data}
                      {...props.gameCallbacks}
                    />
                  ))}
                </Stack>
              </div>
            ) : null}
            {listFinishedGamesQuery.isLoading ? (
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Finished Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  <GameCardSkeleton />
                </Stack>
              </div>
            ) : listFinishedGamesQuery.isError ? (
              <Typography variant="h2">Error</Typography>
            ) : listFinishedGamesQuery.isSuccess ? (
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Finished Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  {listFinishedGamesQuery.data.map((game) => (
                    <GameCard
                      key={game.ID}
                      game={game}
                      user={getRootQuery.data}
                      {...props.gameCallbacks}
                    />
                  ))}
                </Stack>
              </div>
            ) : null}
          </Stack>
        </Stack>
      </PageWrapper>
    </NavigationWrapper>
  );
};

export { HomeScreen };
