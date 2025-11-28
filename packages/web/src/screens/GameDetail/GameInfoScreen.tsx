import React from "react";
import { Alert, Divider, List, ListSubheader, Skeleton, Stack } from "@mui/material";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { IconName } from "../../components/Icon";
import { useNavigate } from "react-router";
import { Table } from "../../components/Table";
import { MemberAvatarGroup } from "../../components/MemberAvatarGroup";
import { useSelectedGameContext } from "../../context";
import { GameMap, Panel } from "../../components";
import { service } from "../../store";

const GameInfoScreen: React.FC = () => {
  const { gameId, gameRetrieveQuery: query } = useSelectedGameContext();
  const navigate = useNavigate();

  const listVariantsQuery = service.endpoints.variantsList.useQuery();

  const handlePlayerInfo = () => {
    navigate(`/game/${gameId}/player-info`);
  };

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
          title="Game Info"
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
                <ListSubheader>Game settings</ListSubheader>
                <Table
                  rows={[
                    {
                      label: "Variant",
                      value: query.data ? (
                        variant?.name
                      ) : (
                        <Stack alignItems="flex-end">
                          <Skeleton variant="text" width={100} />
                        </Stack>
                      ),
                      icon: IconName.WinCondition,
                    },
                    {
                      label: "Phase deadlines",
                      value: query.data ? (
                        query.data.movementPhaseDuration
                      ) : (
                        <Stack alignItems="flex-end">
                          <Skeleton variant="text" width={100} />
                        </Stack>
                      ),
                      icon: IconName.StartYear,
                    },
                    {
                      label: "Visibility",
                      value: query.data ? (
                        query.data.private ? (
                          "Private"
                        ) : (
                          "Public"
                        )
                      ) : (
                        <Stack alignItems="flex-end">
                          <Skeleton variant="text" width={60} />
                        </Stack>
                      ),
                      icon: IconName.Lock,
                    },
                  ]}
                />
                <Divider />
                <ListSubheader>Player settings</ListSubheader>
                <Table
                  rows={[
                    {
                      label: "Players",
                      value:
                        query.data && variant ? (
                          <MemberAvatarGroup
                            members={query.data.members}
                            variant={variant.id}
                            victory={query.data.victory}
                            onClick={handlePlayerInfo}
                          />
                        ) : (
                          <Skeleton
                            variant="rectangular"
                            width={100}
                            height={40}
                          />
                        ),
                      icon: IconName.Players,
                    },
                  ]}
                />
                <Divider />
                <ListSubheader>Variant details</ListSubheader>
                <Table
                  rows={[
                    {
                      label: "Number of nations",
                      value: query.data ? (
                        variant?.nations.length.toString()
                      ) : (
                        <Skeleton variant="text" width={10} />
                      ),
                      icon: IconName.Players,
                    },
                    {
                      label: "Start year",
                      value:
                        query.data && variant ? (
                          variant?.templatePhase.year?.toString()
                        ) : (
                          <Skeleton variant="text" width={50} />
                        ),
                      icon: IconName.StartYear,
                    },
                    {
                      label: "Original author",
                      value:
                        query.data && variant ? (
                          variant?.author
                        ) : (
                          <Skeleton variant="text" width={100} />
                        ),
                      icon: IconName.Author,
                    },
                  ]}
                />
              </List>
            </Stack>
          </Panel.Content>
        </Panel>
      }
    />
  );
};

export { GameInfoScreen };
