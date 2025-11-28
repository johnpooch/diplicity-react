import React from "react";
import {
  Alert,
  ListItem,
  ListItemAvatar,
  Skeleton,
  Stack,
} from "@mui/material";
import { HomeLayout } from "./Layout";
import { service } from "../../store";
import { HomeAppBar } from "./AppBar";
import { useNavigate, useParams } from "react-router";
import { GameMenu } from "../../components/GameMenu";
import { PlayerCard } from "../../components";
import { useCurrentPhase } from "../../hooks";

const PlayerInfo: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });
  const currentPhaseQuery = useCurrentPhase({
    id: gameId,
    phases: query.data?.phases.map(phase => phase.id) ?? [],
  });

  console.log("currentPhaseQuery.data");
  console.log(currentPhaseQuery.data);

  const navigate = useNavigate();

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={
        <HomeAppBar
          title="Player Info"
          onNavigateBack={() => navigate("/")}
          rightButton={
            query.data && (
              <GameMenu
                game={query.data}
                onClickGameInfo={() => navigate(`/game-info/${gameId}`)}
                onClickPlayerInfo={() => navigate(`/player-info/${gameId}`)}
              />
            )
          }
        />
      }
      bottomNavigation={<div></div>}
      content={
        <Stack>
          <>
            {query.data && query.data.status === "pending" && (
              <Alert severity="info">
                This game has not started yet. The game will start once{" "}
                {query.data.variant.nations.length} players have joined.
              </Alert>
            )}
            {query.data && query.data.victory && (
              <Alert severity="success">
                {query.data.victory.type === "solo"
                  ? `${query.data.victory.members[0]?.name} has won the game!`
                  : `The game ended in a draw between ${query.data.victory.members.length} players.`}
              </Alert>
            )}
            {query.data
              ? query.data.members.map(member => (
                  <PlayerCard
                    key={member.id}
                    member={member}
                    variant={query.data.variant.id}
                    phase={currentPhaseQuery.data}
                    victory={query.data.victory}
                  />
                ))
              : Array.from({ length: 3 }, (_, index) => (
                  <ListItem key={index}>
                    <ListItemAvatar>
                      <Skeleton variant="circular" width={40} height={40} />
                    </ListItemAvatar>
                    <Skeleton variant="text" width={150} />
                  </ListItem>
                ))}
          </>
        </Stack>
      }
    />
  );
};

export { PlayerInfo };
