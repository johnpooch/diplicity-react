import React from "react";
import {
  Alert,
  Divider,
  List,
  ListItem,
  ListSubheader,
  Skeleton,
  Stack,
} from "@mui/material";
import { HomeLayout } from "./Layout";
import { GameListRead, service } from "../../store";
import { HomeAppBar } from "./AppBar";
import { IconName } from "../../components/Icon";
import { useNavigate, useParams } from "react-router";
import { Table } from "../../components/Table";
import { InteractiveMap } from "../../components/InteractiveMap/InteractiveMap";
import { MapSkeleton } from "../../components/MapSkeleton";
import { getCurrentPhase } from "../../util";
import { GameMenu } from "../../components/GameMenu";
import { MemberAvatarGroup } from "../../components/MemberAvatarGroup";

const GameInfo: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const query = service.endpoints.gameRetrieve.useQuery({ gameId });
  const navigate = useNavigate();

  const handlePlayerInfo = () => {
    navigate(`/player-info/${gameId}`);
  };

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={
        <HomeAppBar
          title="Game Info"
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
            <List>
              <ListSubheader>Game settings</ListSubheader>
              <Table
                rows={[
                  {
                    label: "Variant",
                    value: query.data ? (
                      query.data.variant.name
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
                    value: query.data ? (
                      <MemberAvatarGroup
                        members={query.data.members}
                        variant={query.data.variant.id}
                        onClick={handlePlayerInfo}
                      />
                    ) : (
                      <Skeleton variant="rectangular" width={100} height={40} />
                    ),
                    icon: IconName.Players,
                  },
                ]}
              />
              <Divider />
              <ListSubheader>Variant details</ListSubheader>
              <ListItem>
                {query.data ? (
                  <InteractiveMap
                    variant={query.data.variant}
                    phase={getCurrentPhase(query.data.phases)}
                    orders={[]}
                    selected={[]}
                  />
                ) : (
                  <MapSkeleton />
                )}
              </ListItem>
              <Table
                rows={[
                  {
                    label: "Number of nations",
                    value: query.data ? (
                      query.data.variant.nations.length.toString()
                    ) : (
                      <Skeleton variant="text" width={10} />
                    ),
                    icon: IconName.Players,
                  },
                  {
                    label: "Start year",
                    value: query.data ? (
                      query.data.variant.templatePhase.year?.toString()
                    ) : (
                      <Skeleton variant="text" width={50} />
                    ),
                    icon: IconName.StartYear,
                  },
                  {
                    label: "Original author",
                    value: query.data ? (
                      query.data.variant.author
                    ) : (
                      <Skeleton variant="text" width={100} />
                    ),
                    icon: IconName.Author,
                  },
                ]}
              />
            </List>
          </>
        </Stack>
      }
    />
  );
};

export { GameInfo };
