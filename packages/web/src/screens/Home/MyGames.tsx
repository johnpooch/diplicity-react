import React, { useEffect } from "react";
import { Stack } from "@mui/material";
import { HomeLayout } from "./Layout";
import { createUseStyles } from "../../components/utils/styles";
import { useState } from "react";
import { Tabs } from "../../components/Tabs";
import { DiplicityLogo } from "../../components/DiplicityLogo";
import { service } from "../../store";
import { NotificationBanner } from "../../components/NotificationBanner";
import { GameCard } from "../../components/GameCard";
import { GameCardSkeleton } from "../../components/GameCardSkeleton";
import { Notice } from "../../components/Notice";
import { IconName } from "../../components/Icon";

const useStyles = createUseStyles(() => ({
  header: {
    paddingTop: 1,
    alignItems: "center",
  },
  image: {
    height: 48,
    width: 48,
  },
  tabs: {
    width: "100%",
  },
}));

const statuses = [
  { value: "pending", label: "Staging" },
  { value: "active", label: "Started" },
  { value: "completed", label: "Finished" },
];

const getStatusMessage = (status: Status) => {
  switch (status) {
    case "pending":
      return "You are not a member of any staging games. Go to Find Games to join a game.";
    case "active":
      return "You are not a member of any started games. When you join a game, it will be in a pending state until the required number of players have joined.";
    case "completed":
      return "You have not finished any games. When a game is finished, it will appear here.";
  }
};

// Priority order for which status to select if there are games in that status
const statusPriority = ["active", "pending", "completed"] as const;

type Status = (typeof statuses)[number]["value"];

const MyGames: React.FC = props => {
  const styles = useStyles(props);
  const [selectedStatus, setSelectedStatus] = useState<Status>("active");

  const query = service.endpoints.gamesList.useQuery({ mine: true });

  useEffect(() => {
    if (query.data) {
      const firstStatusWithGames = statusPriority.find(status =>
        query.data!.some(game => game.status === status)
      );
      if (firstStatusWithGames) {
        setSelectedStatus(firstStatusWithGames);
      }
    }
  }, [query.data]);

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={
        <Stack sx={styles.header}>
          <DiplicityLogo />
          <Tabs
            value={selectedStatus}
            onChange={(_, value) => setSelectedStatus(value)}
            options={statuses}
          />
        </Stack>
      }
      content={
        <Stack>
          <NotificationBanner />
          {query.isLoading
            ? Array.from({ length: 3 }, (_, index) => (
              <GameCardSkeleton key={index} />
            ))
            : query.data
              ? (() => {
                const filteredGames = query.data.filter(
                  game => game.status === selectedStatus
                );
                if (filteredGames.length === 0) {
                  return (
                    <Notice
                      title={`No ${selectedStatus.toLowerCase()} games`}
                      message={getStatusMessage(selectedStatus)}
                      icon={IconName.Empty}
                    />
                  );
                }
                return filteredGames.map(game => (
                  <GameCard key={game.id} {...game} />
                ));
              })()
              : null}
        </Stack>
      }
    />
  );
};

export { MyGames };
