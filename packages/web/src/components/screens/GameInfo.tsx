import React from "react";
import {
  Alert,
  Avatar,
  AvatarGroup,
  Button,
  Divider,
  List,
  ListItem,
  ListSubheader,
  Skeleton,
  Stack,
} from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { service } from "../../store";
import { HomeAppBar } from "../composites/HomeAppBar";
import { IconName } from "../elements/Icon";
import { useNavigate, useParams } from "react-router";
import { Table } from "../elements/Table";
import { InteractiveMap } from "../interactive-map/interactive-map";
import { MapSkeleton } from "../composites/MapSkeleton";
import { getCurrentPhase } from "../../util";

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
        <HomeAppBar title="Game Info" onNavigateBack={() => navigate(-1)} />
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
                ]}
              />
              <Divider />
              <ListSubheader>Player settings</ListSubheader>
              <Table
                rows={[
                  {
                    label: "Players",
                    value: query.data ? (
                      <Button onClick={handlePlayerInfo}>
                        <AvatarGroup total={query.data.members.length} max={7}>
                          {query.data.members.map(member => (
                            <Avatar
                              key={member.username}
                              src={member.picture}
                              sx={{ width: 24, height: 24 }}
                            />
                          ))}
                        </AvatarGroup>
                      </Button>
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
                      query.data.variant.start?.year?.toString() || "TODO"
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
