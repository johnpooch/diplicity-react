import React from "react";
import { Stack } from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { service } from "../../store";
import { NotificationBanner } from "../notification-banner";
import { GameCard } from "../game-card";
import { GameCardSkeleton } from "../composites/GameCardSkeleton";
import { HomeAppBar } from "../composites/HomeAppBar";
import { Notice } from "../elements/Notice";
import { IconName } from "../elements/Icon";

const FindGames: React.FC = () => {
  const query = service.endpoints.gamesList.useQuery({ canJoin: true });

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={<HomeAppBar title="Find Games" />}
      content={
        <Stack>
          <NotificationBanner />
          {query.isLoading ? (
            Array.from({ length: 3 }, (_, index) => (
              <GameCardSkeleton key={index} />
            ))
          ) : query.data?.length === 0 ? (
            <Notice
              title="No games found"
              message="There are no games available to join. Go to Create Game to start a new game."
              icon={IconName.NoResults}
            />
          ) : (
            query.data?.map(game => <GameCard key={game.id} {...game} />)
          )}
        </Stack>
      }
    />
  );
};

export { FindGames };
