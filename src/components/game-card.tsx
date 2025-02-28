import React from "react";
import {
  Avatar,
  Button,
  Link,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router";
import { service } from "../common";
import { GameMenu } from "./game-menu";

const MAX_AVATARS = 10;

const GameCard: React.FC<{
  game: (typeof service.endpoints.listGames.Types.ResultType)[number];
}> = ({ game }) => {
  const navigate = useNavigate();

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.ID}`);
  };

  const handleClickPlayerInfo = () => {
    navigate(`/player-info/${game.ID}`);
  };

  const handleClickGame = () => {
    if (game.Started) {
      navigate(`/game/${game.ID}`);
    } else {
      navigate(`/game-info/${game.ID}`);
    }
  };

  const hasExtraMembers = game.Members.length > MAX_AVATARS;

  return (
    <ListItem
      sx={styles.listItem}
      secondaryAction={
        <GameMenu
          gameId={game.ID}
          onClickGameInfo={handleClickGameInfo}
          onClickPlayerInfo={handleClickPlayerInfo}
        />
      }
    >
      <Link underline="hover" onClick={handleClickGame}>
        <ListItemAvatar sx={styles.mapContainer}>
          <img
            style={{ maxWidth: "100%", maxHeight: "100%" }}
            src={`https://diplicity-engine.appspot.com/Variant/${game.Variant}/Map.svg`}
            alt={game.Variant}
          />
        </ListItemAvatar>
      </Link>
      <Stack>
        <ListItemText
          primary={
            <Link underline="hover" onClick={handleClickGame}>
              {game.Desc}
            </Link>
          }
        />
        <Stack sx={styles.secondaryContainer}>
          <Stack sx={styles.rulesContainer}>
            <Typography variant="caption">{game.Variant}</Typography>
            <Typography variant="caption">{game.PhaseLengthMinutes}</Typography>
          </Stack>
          <Button sx={styles.avatarStackButton} onClick={handleClickPlayerInfo}>
            <Stack
              sx={styles.avatarStackContainer}
              direction="row"
              spacing={-1}
            >
              {game.Members.slice(0, MAX_AVATARS).map((member, index) => (
                <Avatar
                  sx={styles.avatar}
                  key={index}
                  src={member.User.Picture}
                />
              ))}
            </Stack>
            {hasExtraMembers && (
              <Typography variant="body1" sx={styles.extraMembersText}>
                +{game.Members.length - MAX_AVATARS}
              </Typography>
            )}
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
