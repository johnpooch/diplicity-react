import React from "react";
import {
  Alert,
  List,
  ListItem,
  ListItemAvatar,
  Skeleton,
  Stack,
} from "@mui/material";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { useNavigate } from "react-router";
import { useSelectedGameContext, useSelectedPhaseContext } from "../../context";
import { GameMap, Panel, PlayerCard } from "../../components";
import { service } from "../../store";

const PlayerInfoScreen: React.FC = () => {
  const { gameId, gameRetrieveQuery: query } = useSelectedGameContext();
  const { selectedPhase } = useSelectedPhaseContext();

  const listVariantsQuery = service.endpoints.variantsList.useQuery();

  const currentPhaseQuery = service.endpoints.gamePhaseRetrieve.useQuery({
    gameId: gameId ?? "",
    phaseId: selectedPhase,
  });

  const navigate = useNavigate();

  if (query.isError || listVariantsQuery.isError) {
    return <div>Error</div>;
  }

  const variant = listVariantsQuery.data?.find(
    v => v.id === query.data?.variantId
  );

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
                {query.data && variant ? (
                  <>
                    {query.data.members.map(member => (
                      <PlayerCard
                        key={member.id}
                        member={member}
                        variant={variant.id}
                        phase={currentPhaseQuery.data}
                        victory={query.data?.victory}
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
