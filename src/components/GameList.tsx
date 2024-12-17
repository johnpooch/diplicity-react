import { Divider, Stack, Typography } from "@mui/material";
import GameCardSkeleton from "./GameCardSkeleton";
import service from "../common/store/service";
import GameCard from "./GameCard";
import { createGameDisplay } from "../common/display";

const GameList: React.FC<{
  my: boolean;
  status: "Staging" | "Started" | "Finished" | "Open";
  mastered: boolean;
  emptyMessage?: string | JSX.Element;
}> = ({ my, status, mastered, emptyMessage }) => {
  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
  const listGamesQuery = service.endpoints.listGames.useQuery({
    my,
    status,
    mastered,
  });
  const rootQuery = service.endpoints.getRoot.useQuery(undefined);

  const isLoading =
    listVariantsQuery.isLoading ||
    listGamesQuery.isLoading ||
    rootQuery.isLoading;

  const isSuccess =
    listVariantsQuery.isSuccess &&
    listGamesQuery.isSuccess &&
    rootQuery.isSuccess;

  if (isLoading) {
    return (
      <Stack spacing={1} style={{ paddingTop: 12 }}>
        <GameCardSkeleton />
      </Stack>
    );
  }

  if (!isSuccess) {
    return (
      <Typography variant="body1" style={{ textAlign: "left" }}>
        Error
      </Typography>
    );
  }

  return (
    <Stack spacing={1} style={{ paddingTop: 12 }}>
      {isLoading ? (
        <>
          <GameCardSkeleton />
          <Divider />
        </>
      ) : listGamesQuery.data.length === 0 ? (
        <Typography variant="body1" style={{ textAlign: "left" }}>
          {emptyMessage || "No games found"}
        </Typography>
      ) : (
        listGamesQuery.data?.map((game) => (
          <>
            <GameCard
              key={game.ID}
              {...createGameDisplay(
                game,
                listVariantsQuery.data,
                rootQuery.data
              )}
            />
            <Divider />
          </>
        ))
      )}
    </Stack>
  );
};

export default GameList;
