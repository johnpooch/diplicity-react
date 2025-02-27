import React from "react";
import { List, Stack, Tab, Tabs, Typography, Avatar } from "@mui/material";
import {
  AddCircleOutline as StagingIcon,
  PlayCircleOutline as StartedIcon,
  StopCircleOutlined as FinishedIcon,
} from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { mergeQueries, service } from "../../common";
import { GameCard } from "../../components";

const styles: Styles = {
  header: (theme) => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
    paddingTop: 1,
  }),
  iconContainer: {
    width: "100%",
    px: 2,
  },
  tabs: {
    width: "100%",
  },
};

const useMyGames = () => {
  const options = { my: true, mastered: false };
  const { endpoints } = service;
  const rootQuery = endpoints.getRoot.useQuery(undefined);
  const listStagingGamesQuery = endpoints.listGames.useQuery({
    ...options,
    status: "Staging",
  });
  const listStartedGamesQuery = endpoints.listGames.useQuery({
    ...options,
    status: "Started",
  });
  const listFinishedGamesQuery = endpoints.listGames.useQuery({
    ...options,
    status: "Finished",
  });
  const query = mergeQueries(
    [rootQuery, listStagingGamesQuery, listStartedGamesQuery, listFinishedGamesQuery],
    (rootData, stagingGames, startedGames, finishedGames) => {
      return {
        rootData,
        stagingGames,
        startedGames,
        finishedGames,
      };
    }
  );
  return { query };
};

const statuses = [
  { value: "staging", label: "Staging", icon: <StagingIcon /> },
  { value: "started", label: "Started", icon: <StartedIcon /> },
  { value: "finished", label: "Finished", icon: <FinishedIcon /> },
] as const;

type Status = (typeof statuses)[number]["value"];

const MyGames: React.FC = () => {
  const { query } = useMyGames();
  const [selectedStatus, setSelectedStatus] = React.useState<
    Status | undefined
  >(undefined);

  const status = query.data
    ? selectedStatus
      ? selectedStatus
      : query.data?.startedGames.length > 0
      ? "started"
      : query.data?.stagingGames.length > 0
      ? "staging"
      : "finished"
    : "started";

  return (
    <Stack>
      <Stack sx={styles.header}>
        <Tabs
          value={status}
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
        <QueryContainer query={query}>
          {(data) => {
            const games =
              status === "staging"
                ? data.stagingGames
                : status === "started"
                ? data.startedGames
                : data.finishedGames;

            if (games.length === 0) {
              return (
                <Stack spacing={1} padding={2}>
                  <Typography variant="body2" sx={styles.noGamesText}>
                    You are not a member of any {status} games.
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

            return games.map((game) => <GameCard key={game.ID} game={game} />);
          }}
        </QueryContainer>
      </List>
    </Stack>
  );
};

export { MyGames };
