import React from "react";
import {
  Alert,
  ListItem,
  ListItemAvatar,
  Skeleton,
  Stack,
} from "@mui/material";
import { HomeLayout } from "./Layout";
import { GameListRead, service } from "../../store";
import { HomeAppBar } from "./AppBar";
import { useNavigate, useParams } from "react-router";
import { GameMenu } from "../../components/GameMenu";
import { PlayerCard } from "../../components";

const PlayerInfo: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });
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
                game={query.data as GameListRead}
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
            {query.data
              ? query.data.members.map(member => (
                  <PlayerCard
                    key={member.id}
                    member={member}
                    variant={query.data.variant.id}
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
