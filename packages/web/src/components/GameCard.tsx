import React from "react";
import {
  AvatarGroup,
  Button,
  Link,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router";
import { service } from "../store";
import { GameMenu } from "./GameMenu";
import { InteractiveMap } from "./InteractiveMap/InteractiveMap";
import { getCurrentPhase } from "../util";
import { createUseStyles } from "./utils/styles";
import { PlayerAvatar } from "./PlayerAvatar";
import { Icon, IconName } from "./Icon";

const MAX_AVATARS = 10;

type GameCardProps = (typeof service.endpoints.gamesList.Types.ResultType)[number];

const useStyles = createUseStyles<GameCardProps>(() => ({
  listItem: (theme) => ({
    gap: 1,
    borderBottom: `1px solid ${theme.palette.divider}`,
    alignItems: "center",
  }),
  mapContainer: {
    display: "flex",
    width: 80,
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
    padding: "8px 0px 8px 0px",
  },
  avatarStackContainer: {
    alignItems: "center",
  },
  avatar: {
    width: 24,
    height: 24,
  },
  extraMembersText: {
    marginLeft: "4px",
  },
  privateIcon: {
    fontSize: 14,
    opacity: 0.6,
  },
}));

const GameCard: React.FC<GameCardProps> = (game) => {
  const navigate = useNavigate();
  const styles = useStyles(game);
  const currentPhase = getCurrentPhase(game.phases);

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.id}`);
  };

  const handleClickPlayerInfo = () => {
    navigate(`/player-info/${game.id}`);
  };

  const handleClickGame = () => {
    if (game.status === "active") {
      navigate(`/game/${game.id}`);
    } else {
      navigate(`/game-info/${game.id}`);
    }
  };

  return (
    <ListItem
      sx={styles.listItem}
      secondaryAction={
        <GameMenu
          game={game}
          onClickGameInfo={handleClickGameInfo}
          onClickPlayerInfo={handleClickPlayerInfo}
        />
      }
    >
      <Link underline="hover" onClick={handleClickGame}>
        <ListItemAvatar sx={styles.mapContainer}>
          <InteractiveMap
            variant={game.variant}
            phase={currentPhase}
            orders={[]}
            selected={[]}
          />
        </ListItemAvatar>
      </Link>
      <Stack>
        <ListItemText
          primary={
            <Stack direction="row" alignItems="center" gap={1}>
              {game.private && (
                <Icon
                  name={IconName.Lock}
                  sx={styles.privateIcon}
                />
              )}
              <Link underline="hover" onClick={handleClickGame}>
                {game.name}
              </Link>
            </Stack>
          }
        />
        <Stack sx={styles.secondaryContainer}>
          <Stack sx={styles.rulesContainer}>
            <Typography variant="caption">{game.variant.name}</Typography>
            <Typography variant="caption">
              {game.movementPhaseDuration}
            </Typography>
          </Stack>
          <Button sx={styles.avatarStackButton} onClick={handleClickPlayerInfo}>
            <AvatarGroup total={game.members.length}>
              {game.members.slice(0, MAX_AVATARS).map((member, index) => (
                <PlayerAvatar member={member} variant={game.variant.id} size="small" key={index} />
              ))}
            </AvatarGroup>
          </Button>
        </Stack>
      </Stack>
    </ListItem >
  );
};


export { GameCard };
