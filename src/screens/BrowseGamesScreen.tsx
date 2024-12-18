import React from "react";
import { Stack, Typography } from "@mui/material";
import { GameCard, GameCallbacks } from "../components/GameCard";
import NavigationWrapper from "../components/NavigationWrapper";
import PageWrapper from "../components/PageWrapper";
import service from "../common/store/service";
import GameCardSkeleton from "../components/GameCardSkeleton";

const BrowseGamesScreen: React.FC<{
  gameCallbacks: GameCallbacks;
}> = (props) => {
  const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
  const listStagingGamesQuery = service.endpoints.listGames.useQuery({
    my: false,
    status: "Staging",
    mastered: false,
  });

  if (!getRootQuery.isSuccess) {
    return null;
  }

  return (
    <NavigationWrapper>
      <PageWrapper>
        <Stack>
          <Typography variant="h1">Browse games</Typography>
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
          </Stack>
        </Stack>
      </PageWrapper>
    </NavigationWrapper>
  );
};

export { BrowseGamesScreen };
