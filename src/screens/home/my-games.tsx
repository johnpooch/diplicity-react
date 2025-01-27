import React from "react";
import {
  Avatar,
  Box,
  Button,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Stack,
  styled,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import {
  MoreHoriz as MenuIcon,
  AddCircleOutline as StagingIcon,
  PlayCircleOutline as StartedIcon,
  StopCircleOutlined as FinishedIcon,
  SportsMotorsports as DiplicityIcon,
} from "@mui/icons-material";
import { QueryContainer } from "../../components";

import { mergeQueries, service } from "../../common";

const options = { my: true, mastered: false };

const useMyGames = () => {
  const { endpoints } = service;
  const listVariantsQuery = endpoints.listVariants.useQuery(undefined);
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
    [
      listVariantsQuery,
      listStagingGamesQuery,
      listStartedGamesQuery,
      listFinishedGamesQuery,
    ],
    (variants, stagingGames, startedGames, finishedGames) => {
      const getMapSvgUrl = (game: (typeof stagingGames)[number]) => {
        const variant = variants.find(
          (variant) => variant.Name === game.Variant
        );
        return variant?.Links?.find((link) => link.Rel === "map")?.URL;
      };
      return {
        getMapSvgUrl,
        stagingGames,
        startedGames,
        finishedGames,
      };
    }
  );
  return { query };
};

const StyledTabs = styled((props: React.ComponentProps<typeof Tabs>) => (
  <Tabs
    {...props}
    TabIndicatorProps={{ children: <span className="MuiTabs-indicatorSpan" /> }}
  />
))(({ theme }) => ({
  "& .MuiTabs-indicator": {
    display: "flex",
    justifyContent: "center",
    backgroundColor: "transparent",
  },
  "& .MuiTabs-indicatorSpan": {
    maxWidth: 40,
    width: "100%",
    backgroundColor: theme.palette.primary.main,
  },
}));

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
    <List sx={{ width: "100%" }} disablePadding>
      <ListItem divider disablePadding>
        <Box sx={{ width: "100%" }}>
          <Stack alignItems="center">
            <DiplicityIcon fontSize="large" />
            <StyledTabs
              value={status}
              onChange={(_, value) => setSelectedStatus(value)}
              variant="fullWidth"
              sx={{ width: "100%" }}
            >
              {statuses.map((status) => (
                <Tab disableRipple value={status.value} label={status.label} />
              ))}
            </StyledTabs>
          </Stack>
        </Box>
      </ListItem>
      <QueryContainer query={query}>
        {(data) => {
          const games =
            status === "staging"
              ? data.stagingGames
              : status === "started"
              ? data.startedGames
              : data.finishedGames;

          return games.map((game) => (
            <ListItem
              alignItems="center"
              divider
              sx={{ gap: 1 }}
              secondaryAction={
                <IconButton edge="end" aria-label="delete">
                  <MenuIcon />
                </IconButton>
              }
            >
              <ListItemAvatar sx={{ display: "flex", minWidth: 80 }}>
                <img
                  src={data.getMapSvgUrl(game)}
                  style={{
                    borderRadius: 2,
                  }}
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
                  <Stack gap={1}>
                    <Stack direction="row" gap={1}>
                      <Typography variant="caption">{game.Variant}</Typography>
                      <Typography variant="caption">
                        {game.PhaseLengthMinutes}
                      </Typography>
                    </Stack>
                    <Button
                      sx={{
                        justifyContent: "flex-start",
                        width: "fit-content",
                      }}
                    >
                      <Stack direction="row" spacing={-1} alignItems="center">
                        {game.Members.map((member) => (
                          <Avatar
                            sx={{
                              width: 24,
                              height: 24,
                            }}
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
  );
};

export { MyGames };
