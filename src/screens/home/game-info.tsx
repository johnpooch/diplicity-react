import React from "react";
import {
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
} from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { mergeQueries, service, useGetVariantQuery } from "../../common";
import { ScreenTopBar } from "./screen-top-bar";
import { useParams } from "react-router";

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
  listItemSecondaryText: (theme) => ({
    color: theme.palette.text.secondary,
    paddingRight: 1,
    "& .MuiListItemText-primary": {
      textAlign: "right",
    },
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

const useGameInfo = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("Game ID not found");

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
  const { query } = useGameInfo();

  const TableListItem: React.FC<{
    label: string;
    value: string | undefined;
    icon: React.ReactElement;
  }> = ({ label, value, icon }) => {
    return (
      <ListItem>
        <ListItemIcon sx={styles.listItemIcon}>{icon}</ListItemIcon>
        <ListItemText primary={label} sx={styles.listItemPrimaryText} />
        <ListItemText primary={value} sx={styles.listItemSecondaryText} />
      </ListItem>
    );
  };

  return (
    <>
      <ScreenTopBar title="Game info" />
      <QueryContainer query={query}>
        {(data) => (
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
                <Button sx={styles.avatarStackButton}>
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
        )}
      </QueryContainer>
    </>
  );
};

export { GameInfo };
