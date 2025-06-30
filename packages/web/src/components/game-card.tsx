import React from "react";
import {
  Avatar,
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
import { GameMenu } from "./game-menu";
import { InteractiveMap } from "./interactive-map/interactive-map";

const MAX_AVATARS = 10;

const GameCard: React.FC<
  (typeof service.endpoints.gamesList.Types.ResultType)[number]
> = (game) => {
  const navigate = useNavigate();

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
          <InteractiveMap variant={game.variant} phase={game.currentPhase} orders={[]} />
        </ListItemAvatar>
      </Link>
      <Stack>
        <ListItemText
          primary={
            <Link underline="hover" onClick={handleClickGame}>
              {game.name}
            </Link>
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
                <Avatar
                  sx={styles.avatar}
                  key={index}
                  src={member.picture}
                />
              ))}
            </AvatarGroup>
          </Button>
        </Stack>
      </Stack>
    </ListItem>
  );
};

const styles: Styles = {
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
};

export { GameCard };
