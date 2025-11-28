import React from "react";
import { Alert, List, ListItem, ListItemAvatar, Skeleton, Stack } from "@mui/material";
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
              {query.data && query.data.victory && (
                <Alert severity="success">
                  {query.data.victory.type === "solo"
                    ? `${query.data.victory.members[0]?.name} has won the game!`
                    : `The game ended in a draw between ${query.data.victory.members.length} players.`}
                </Alert>
              )}
              <List>
                {query.data ? (
                  <>
                    {query.data.members.map(member => (
                      <PlayerCard
                        key={member.id}
                        member={member}
                        variant={query.data.variant.id}
                        phase={currentPhaseQuery.data}
                        victory={query.data.victory}
                      />
                    ))}
                  </>
                ) : (
                  <>
                    {Array.from({ length: 3 }, (_, index) => (
                      <ListItem key={index}>
                        <ListItemAvatar>
                          <Skeleton variant="circular" width={40} height={40} />
                        </ListItemAvatar>
                        <Skeleton variant="text" width={150} />
                      </ListItem>
                    ))}
                  </>
                )}
              </List>
            </Stack>
          </Panel.Content>
        </Panel>
      }
    />
  );
};

export { PlayerInfoScreen };
