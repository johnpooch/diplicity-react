import React from "react";
import { Stack } from "@mui/material";
import { HomeLayout } from "./Layout";
import { service } from "../../store";
import { NotificationBanner } from "../../components/NotificationBanner";
import { GameCard } from "../../components/GameCard";
import { HomeAppBar } from "./AppBar";
import { Notice } from "../../components/Notice";
import { IconName } from "../../components/Icon";
import { useNavigate } from "react-router";

const FindGames: React.FC = () => {
  const query = service.endpoints.gamesList.useQuery({ canJoin: true });
  const navigate = useNavigate();

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={<HomeAppBar title="Find Games" onNavigateBack={() => navigate("/")} />}
      content={
        <Stack>
          <NotificationBanner />
          {query.isLoading ? (
            Array.from({ length: 3 }, (_, index) => (
              <GameCard key={index} />
            ))
          ) : query.data?.length === 0 ? (
            <Notice
              title="No games found"
              message="There are no games available to join. Go to Create Game to start a new game."
              icon={IconName.NoResults}
            />
          ) : (
            query.data?.map(game => <GameCard key={game.id} game={game} />)
          )}
        </Stack>
      }
    />
  );
};

export { FindGames };
