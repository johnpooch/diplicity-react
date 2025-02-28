import React from "react";
import {
  Alert,
  Avatar,
  Button,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Stack,
} from "@mui/material";
import {
  Map as VariantIcon,
  TimerOutlined as DeadlinesIcon,
  Language as LanguageIcon,
  People as PlayersIcon,
  Flag as WinConditionIcon,
  CalendarToday as StartYearIcon,
  Person as AuthorIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { QueryContainer, TableListItem } from "../../components";
import {
  mergeQueries,
  service,
  useGetVariantQuery,
  useSelectedGameContext,
} from "../../common";
import { useNavigate } from "react-router";

const useGameInfo = () => {
  const { gameId } = useSelectedGameContext();

  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const getVariantQuery = useGetVariantQuery(gameId);

  const query = mergeQueries(
    [getGameQuery, getVariantQuery],
    (game, variant) => {
      return {
        game,
        variant,
      };
    }
  );

  return { query };
};

const GameInfo: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const { query } = useGameInfo();
  const navigate = useNavigate();

  const handlePlayerInfo = () => {
    navigate(`../player-info/${gameId}`);
  };

  return (
    <QueryContainer query={query}>
      {(data) => (
        <>
          {!data.game.Started && (
            <Alert severity="info" icon={<InfoIcon />}>
              This game has not started yet. The game will start once{" "}
              {data.variant.Nations.length} players have joined.
            </Alert>
          )}
          <List>
            <ListSubheader sx={styles.listSubheader}>
              Game settings
            </ListSubheader>
            <TableListItem
              label="Variant"
              value={data.variant.Name}
              icon={<VariantIcon />}
            />
            <TableListItem
              label="Phase deadlines"
              value={data.game.PhaseLengthMinutes}
              icon={<DeadlinesIcon />}
            />
            {data.game.NonMovementPhaseLengthMinutes && (
              <TableListItem
                label="Non-movement phase deadlines"
                value={data.game.PhaseLengthMinutes}
                icon={<></>}
              />
            )}
            <Divider />
            <ListSubheader sx={styles.listSubheader}>
              Player settings
            </ListSubheader>
            {data.game.ChatLanguageISO639_1 && (
              <TableListItem
                label="Language"
                value={data.game.ChatLanguageISO639_1}
                icon={<LanguageIcon />}
              />
            )}
            <ListItem
              secondaryAction={
                <Button
                  sx={styles.avatarStackButton}
                  onClick={handlePlayerInfo}
                >
                  <Stack
                    sx={styles.avatarStackContainer}
                    direction="row"
                    spacing={-1}
                  >
                    {data.game.Members.map((member) => (
                      <Avatar
                        sx={styles.avatar}
                        key={member.User.Id}
                        src={member.User.Picture}
                      />
                    ))}
                  </Stack>
                </Button>
              }
            >
              <ListItemIcon sx={styles.listItemIcon}>
                <PlayersIcon />
              </ListItemIcon>
              <ListItemText
                primary={"Players"}
                sx={styles.listItemPrimaryText}
              />
            </ListItem>
            <Divider />
            <ListSubheader sx={styles.listSubheader}>
              Variant details
            </ListSubheader>
            <ListItem>
              <img
                src={`https://diplicity-engine.appspot.com/Variant/${data.variant.Name}/Map.svg`}
                alt={data.variant.Name}
                style={{ width: "100%" }}
              />
            </ListItem>
            <TableListItem
              label="Number of nations"
              value={data.variant.Nations.length.toString()}
              icon={<PlayersIcon />}
            />
            <TableListItem
              label="Start year"
              value={data.variant.Start.Year.toString()}
              icon={<StartYearIcon />}
            />
            <TableListItem
              label="Original author"
              value={data.variant.CreatedBy}
              icon={<AuthorIcon />}
            />
            <ListItem>
              <ListItemIcon sx={styles.listItemIcon}>
                <WinConditionIcon />
              </ListItemIcon>
              <ListItemText
                primary={"Win condition"}
                secondary={data.variant.Rules}
                sx={styles.listItemPrimaryText}
              />
            </ListItem>
            <Divider />
          </List>
        </>
      )}
    </QueryContainer>
  );
};

const styles: Styles = {
  listSubheader: (theme) => ({
    textAlign: "left",
    color: theme.palette.text.primary,
  }),
  listItemIcon: (theme) => ({
    color: theme.palette.text.primary,
    minWidth: "fit-content",
    padding: 1,
  }),
  listItemPrimaryText: (theme) => ({
    color: theme.palette.text.primary,
  }),
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
};

export { GameInfo };
