import React from "react";
import {
  Avatar,
  Button,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import {
  MoreHoriz as MenuIcon,
  AddCircleOutline as StagingIcon,
  PlayCircleOutline as StartedIcon,
  StopCircleOutlined as FinishedIcon,
} from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { mergeQueries, service } from "../../common";

const styles: Styles = {
  header: (theme) => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
    alignItems: "center",
  }),
  headerIcon: {
    fontSize: 48,
  },
  listItem: (theme) => ({
    gap: 1,
    borderBottom: `1px solid ${theme.palette.divider}`,
    alignItems: "center",
  }),
  mapContainer: {
    display: "flex",
    width: 80,
  },
  map: {
    borderRadius: 2,
  },
  secondaryContainer: {
    gap: 1,
  },
  rulesContainer: {
    gap: 1,
    flexDirection: "row",
  },
  avatarStackButton: {
    justifyContent: "flex-start",
    width: "fit-content",
  },
  avatarStackContainer: {
    alignItems: "center",
  },
  avatar: {
    width: 24,
    height: 24,
  },
  noGamesText: {
    textAlign: "center",
  },
  tabs: {
    width: "100%",
  },
};

const useMyGames = () => {
  const options = { my: true, mastered: false };
  const { endpoints } = service;
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
    [listStagingGamesQuery, listStartedGamesQuery, listFinishedGamesQuery],
    (stagingGames, startedGames, finishedGames) => {
      return {
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
    : undefined;

  return (
    <Stack>
      <Stack sx={styles.header}>
        <img
          src="/otto.png"
          alt="Diplicity"
          style={{ height: 54, width: 54 }}
        />
        <Tabs
          value={status}
          onChange={(_, value) => setSelectedStatus(value)}
          variant="fullWidth"
          sx={styles.tabs}
        >
          {statuses.map((status) => (
            <Tab disableRipple value={status.value} label={status.label} />
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

            return games.map((game) => (
              <ListItem
                sx={styles.listItem}
                secondaryAction={
                  <IconButton edge="end" aria-label="delete">
                    <MenuIcon />
                  </IconButton>
                }
              >
                <ListItemAvatar sx={styles.mapContainer}>
                  <img
                    src={`https://diplicity-engine.appspot.com/Variant/${game.Variant}/Map.svg`}
                    alt={game.Variant}
                  />
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Link href="#" underline="hover">
                      <Typography>{game.Desc}</Typography>
                    </Link>
                  }
                  secondary={
                    <Stack sx={styles.secondaryContainer}>
                      <Stack sx={styles.rulesContainer}>
                        <Typography variant="caption">
                          {game.Variant}
                        </Typography>
                        <Typography variant="caption">
                          {game.PhaseLengthMinutes}
                        </Typography>
                      </Stack>
                      <Button sx={styles.avatarStackButton}>
                        <Stack
                          sx={styles.avatarStackContainer}
                          direction="row"
                          spacing={-1}
                        >
                          {game.Members.map((member) => (
                            <Avatar
                              sx={styles.avatar}
                              key={member.User.Id}
                              src={member.User.Picture}
                            />
                          ))}
                        </Stack>
                      </Button>
                    </Stack>
                  }
                />
              </ListItem>
            ));
          }}
        </QueryContainer>
      </List>
    </Stack>
  );
};

export { MyGames };
