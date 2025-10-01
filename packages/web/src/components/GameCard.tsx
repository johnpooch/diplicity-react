import React from "react";
import {
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
import { getCurrentPhase, formatDateTime } from "../util";
import { createUseStyles } from "./utils/styles";
import { MemberAvatarGroup } from "./MemberAvatarGroup";
import { Icon, IconName } from "./Icon";

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
  },
  rulesContainer: {
    gap: 1,
    flexDirection: "row",
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
          {game.status === "active" && (
            <Stack sx={styles.rulesContainer}>
              <Typography variant="caption">
                {currentPhase?.season} {currentPhase?.year} - {currentPhase?.type}
              </Typography>
              <Stack direction="row" alignItems="center" gap={"4px"}>
                <Icon name={IconName.Clock} sx={{ fontSize: 14 }} />
                <Typography variant="caption">
                  {formatDateTime(currentPhase?.scheduledResolution)}
                </Typography>
              </Stack>
            </Stack>
          )}
          <MemberAvatarGroup
            members={game.members}
            variant={game.variant.id}
            onClick={handleClickPlayerInfo}
          />
        </Stack>
      </Stack>
    </ListItem >
  );
};


export { GameCard };
