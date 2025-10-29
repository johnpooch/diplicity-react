import React from "react";
import { List, ListItem, ListItemAvatar, Skeleton, Stack } from "@mui/material";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { useNavigate } from "react-router";
import { useSelectedGameContext } from "../../context";
import { GameMap, Panel, PlayerCard } from "../../components";
import { useCurrentPhase } from "../../hooks";

const PlayerInfoScreen: React.FC = () => {
  const { gameId, gameRetrieveQuery: query } = useSelectedGameContext();
  const currentPhaseQuery = useCurrentPhase({
    id: gameId ?? "",
    phases: query.data?.phases.map(phase => phase.id) ?? [],
  });

  const navigate = useNavigate();

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <GameDetailLayout
      appBar={
        <GameDetailAppBar
          title="Player Info"
          onNavigateBack={() => navigate(`/game/${gameId}`)}
          variant="secondary"
        />
      }
      bottomNavigation={<div></div>}
      rightPanel={<GameMap />}
      content={
        <Panel>
          <Panel.Content>
            <Stack>
              <List>
                {query.data
                  ? query.data.members.map(member => (
                      <PlayerCard
                        key={member.id}
                        member={member}
                        variant={query.data?.variant.id ?? ""}
                        phase={currentPhaseQuery.data}
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
              </List>
            </Stack>
          </Panel.Content>
        </Panel>
      }
    />
  );
};

export { PlayerInfoScreen };
