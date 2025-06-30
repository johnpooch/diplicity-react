import React, { useEffect } from "react";
import { List, Stack, Tab, Tabs, Typography } from "@mui/material";
import {
  AddCircleOutline as StagingIcon,
  PlayCircleOutline as StartedIcon,
  StopCircleOutlined as FinishedIcon,
} from "@mui/icons-material";
import { GameCard, NotificationBanner, QueryContainer } from "../components";
import { service } from "../store";

const statuses = [
  { value: "pending", label: "Staging", icon: <StagingIcon /> },
  { value: "active", label: "Started", icon: <StartedIcon /> },
  { value: "completed", label: "Finished", icon: <FinishedIcon /> },
] as const;

// Priority order for which status to select if there are games in that status
const statusPriority = [
  "active",
  "pending",
  "completed",
] as const;

type Status = (typeof statuses)[number]["value"];

const MyGames: React.FC = () => {
  const query = service.endpoints.gamesList.useQuery({ mine: true });

  const [selectedStatus, setSelectedStatus] = React.useState<Status>("active");

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

  return (
    <Stack>
      <Stack sx={styles.header}>
        <img
          src="/otto.png"
          alt="Diplicity"
          style={{ height: 48, width: 48 }}
        />
        <Tabs
          value={selectedStatus}
          onChange={(_, value) => setSelectedStatus(value)}
          variant="fullWidth"
          sx={styles.tabs}
        >
          {statuses.map((status) => (
            <Tab
              key={status.value}
              disableRipple
              value={status.value}
              label={status.label}
            />
          ))}
        </Tabs>
      </Stack>
      <List>
        <NotificationBanner />
        <QueryContainer query={query}>
          {(games) => {
            if (
              games.filter((game) => game.status === selectedStatus).length ===
              0
            ) {
              return (
                <Stack spacing={1} padding={2}>
                  <Typography variant="body2" sx={styles.noGamesText}>
                    You are not a member of any {selectedStatus} games.
                  </Typography>
                  <Typography variant="body2" sx={styles.noGamesText}>
                    Go to "Find games" to join a game or click "Create game" to
                    start a new game.
                  </Typography>
                  <Typography variant="body2" sx={styles.noGamesText}>
                    Join our Discord server to find other players to play with.
                  </Typography>
                </Stack>
              );
            }
            return games
              .filter((game) => game.status === selectedStatus)
              .map((game) => <GameCard key={game.id} {...game} />);
          }}
        </QueryContainer>
      </List>
    </Stack>
  );
};

const styles: Styles = {
  header: (theme) => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
    alignItems: "center",
  }),
  noGamesText: {
    textAlign: "center",
  },
  tabs: {
    width: "100%",
  },
};

export { MyGames };
