import React from "react";
import { Stack, Typography } from "@mui/material";
import { GameCard, GameCallbacks } from "../components/GameCard";
import { useHomeQuery } from "../common";
import NavigationWrapper from "../components/NavigationWrapper";
import PageWrapper from "../components/PageWrapper";

const HomeScreen: React.FC<{
  useHomeQuery: typeof useHomeQuery;
  gameCallbacks: GameCallbacks;
}> = (props) => {
  const query = props.useHomeQuery();

  if (query.isSuccess) {
    return (
      <NavigationWrapper>
        <PageWrapper>
          <Stack>
            <Typography variant="h1">My games</Typography>
            <Stack spacing={2}>
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Staging Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  {query.data.stagingGames.map((game) => (
                    <GameCard
                      key={game.id}
                      {...game}
                      {...props.gameCallbacks}
                    />
                  ))}
                </Stack>
              </div>
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2" style={{ paddingBottom: 12 }}>
                  Active Games
                </Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  {query.data.startedGames.map((game) => (
                    <GameCard
                      key={game.id}
                      {...game}
                      {...props.gameCallbacks}
                    />
                  ))}
                </Stack>
              </div>
              <div style={{ paddingTop: 24, paddingBottom: 24 }}>
                <Typography variant="h2">Finished Games</Typography>
                <Stack spacing={1} style={{ paddingTop: 12 }}>
                  {query.data.finishedGames.map((game) => (
                    <GameCard
                      key={game.id}
                      {...game}
                      {...props.gameCallbacks}
                    />
                  ))}
                </Stack>
              </div>
            </Stack>
          </Stack>
        </PageWrapper>
      </NavigationWrapper>
    );
  }
};

export { HomeScreen };
