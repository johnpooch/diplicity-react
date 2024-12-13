import { Divider, Stack, Typography } from "@mui/material";
import GameCardSkeleton from "./GameCardSkeleton";
import service from "../common/store/service";
import GameCard from "./GameCard";
import { Game } from "../common";

const transformGame = (game: Game): React.ComponentProps<typeof GameCard> => ({
  id: game.ID,
  title: game.Desc,
  users: game.Members.map((member) => ({
    username: member.User.Name,
    src: member.User.Picture,
  })),
  onClickPlayerInfo: () => alert(`Player info for game ${game.ID}`),
  onClickGameInfo: () => alert(`Game info for game ${game.ID}`),
  onClickShare: () => alert(`Share game ${game.ID}`),
  onClickJoin: () => alert(`Join game ${game.ID}`),
  onClickLeave: () => alert(`Leave game ${game.ID}`),
  status: game.Started ? "active" : game.Finished ? "finished" : "staging",
  private: game.Private,
  canJoin: !game.Started && !game.Finished,
  canLeave: game.Started && !game.Finished,
  variant: game.Variant,
  phaseDuration: `${game.PhaseLengthMinutes} minutes`,
  timeLeft: game.NewestPhaseMeta
    ? `${game.NewestPhaseMeta[0].NextDeadlineIn} minutes`
    : undefined,
  ordersStatus: game.NewestPhaseMeta ? "confirmed" : undefined,
  link: `https://diplicity-engine.appspot.com/games/${game.ID}`,
});

const GameList: React.FC<{
  my: boolean;
  status: "Staging" | "Started" | "Finished" | "Open";
  mastered: boolean;
  emptyMessage?: string;
}> = (props) => {
  const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
  const listGamesQuery = service.endpoints.listGames.useQuery(props);

  const isLoading = listVariantsQuery.isLoading || listGamesQuery.isLoading;

  return (
    <Stack spacing={1} style={{ paddingTop: 12 }}>
      {isLoading ? (
        <>
          <GameCardSkeleton />
          <Divider />
        </>
      ) : listGamesQuery.data?.length === 0 ? (
        <Typography variant="body1" style={{ textAlign: "left" }}>
          {props.emptyMessage || "No games found"}
        </Typography>
      ) : (
        listGamesQuery.data?.map((game) => (
          <>
            <GameCard key={game.ID} {...transformGame(game)} />
            <Divider />
          </>
        ))
      )}
    </Stack>
  );
};

export default GameList;
