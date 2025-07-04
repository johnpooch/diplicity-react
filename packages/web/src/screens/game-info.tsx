import React from "react";
import {
  Alert,
  Avatar,
  AvatarGroup,
  Button,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
} from "@mui/material";
import {
  Map as VariantIcon,
  TimerOutlined as DeadlinesIcon,
  People as PlayersIcon,
  Flag as WinConditionIcon,
  CalendarToday as StartYearIcon,
  Person as AuthorIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { QueryContainer, TableListItem } from "../components";
import { service } from "../store";
import { useNavigate } from "react-router";
import { InteractiveMap } from "../components/interactive-map/interactive-map";
import { useSelectedGameContext } from "../context";
import { getCurrentPhase } from "../util";

const GameInfo: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const query = service.endpoints.gameRetrieve.useQuery({ gameId });
  const navigate = useNavigate();

  const handlePlayerInfo = () => {
    navigate(`../player-info/${gameId}`);
  };

  return (
    <QueryContainer query={query}>
      {(game) => (
        <>
          {game.status === "pending" && (
            <Alert severity="info" icon={<InfoIcon />}>
              This game has not started yet. The game will start once{" "}
              {game.variant.nations.length} players have joined.
            </Alert>
          )}
          <List>
            <ListSubheader sx={styles.listSubheader}>
              Game settings
            </ListSubheader>
            <TableListItem
              label="Variant"
              value={game.variant.name}
              icon={<VariantIcon />}
            />
            <TableListItem
              label="Phase deadlines"
              value={game.movementPhaseDuration}
              icon={<DeadlinesIcon />}
            />
            <Divider />
            <ListSubheader sx={styles.listSubheader}>
              Player settings
            </ListSubheader>
            <ListItem
              secondaryAction={
                <Button
                  sx={styles.avatarStackButton}
                  onClick={handlePlayerInfo}
                >
                  <AvatarGroup total={game.members.length} max={7}>
                    {game.members.map((member) => (
                      <Avatar
                        sx={styles.avatar}
                        key={member.username}
                        src={member.picture}
                      />
                    ))}
                  </AvatarGroup>
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
              <InteractiveMap
                variant={game.variant}
                phase={getCurrentPhase(game.phases)}
                orders={[]}
              />
            </ListItem>
            <TableListItem
              label="Number of nations"
              value={game.variant.nations.length.toString()}
              icon={<PlayersIcon />}
            />
            <TableListItem
              label="Start year"
              value={"TODO"}
              icon={<StartYearIcon />}
            />
            <TableListItem
              label="Original author"
              value={game.variant.author}
              icon={<AuthorIcon />}
            />
            <ListItem>
              <ListItemIcon sx={styles.listItemIcon}>
                <WinConditionIcon />
              </ListItemIcon>
              <ListItemText
                primary={"Win condition"}
                secondary={game.variant.description}
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
