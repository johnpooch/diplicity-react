import React from "react";
import {
  Avatar,
  Button,
  IconButton,
  Link,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import {
  MoreHoriz as MenuIcon,
  Info as InfoIcon,
  Person as PlayerInfoIcon,
  Add as JoinGameIcon,
  Remove as LeaveGameIcon,
  Share as ShareIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router";
import {
  actions,
  service,
  useJoinGameMutation,
  useLeaveGameMutation,
} from "../common";
import { useDispatch } from "react-redux";

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
};

const useGameCard = (
  game: (typeof service.endpoints.listGames.Types.ResultType)[number]
) => {
  const dispatch = useDispatch();
  const [joinGame, joinGameMutation] = useJoinGameMutation(game.ID);
  const [leaveGame, leaveGameMutation] = useLeaveGameMutation(game.ID);

  const isSubmitting =
    joinGameMutation.isLoading || leaveGameMutation.isLoading;

  const handleShare = () => {
    navigator.clipboard.writeText(
      `${window.location.origin}/game-info/${game.ID}`
    );
    dispatch(actions.setFeedback({ message: "Link copied to clipboard" }));
  };

  return { joinGame, leaveGame, isSubmitting, handleShare };
};

const GameCard: React.FC<{
  game: (typeof service.endpoints.listGames.Types.ResultType)[number];
}> = ({ game }) => {
  const navigate = useNavigate();
  const { joinGame, leaveGame, isSubmitting, handleShare } = useGameCard(game);

  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.ID}`);
  };

  const handleClickPlayerInfo = (userId: string) => {
    navigate(`/player-info/${userId}`);
  };

  const handleJoinGame = async () => {
    await joinGame();
  };

  const handleLeaveGame = async () => {
    await leaveGame();
  };

  const handleClickGame = () => {
    if (game.Started) {
      navigate(`/game/${game.ID}`);
    } else {
      navigate(`/game-info/${game.ID}`);
    }
  };

  return (
    <ListItem
      sx={styles.listItem}
      secondaryAction={
        <>
          <IconButton edge="end" aria-label="menu" onClick={handleMenuOpen}>
            <MenuIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem
              onClick={() => {
                handleClickGameInfo();
                handleMenuClose();
              }}
              disabled={isSubmitting}
            >
              <InfoIcon sx={{ marginRight: 1 }} />
              Game info
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleClickPlayerInfo(game.ID);
                handleMenuClose();
              }}
              disabled={isSubmitting}
            >
              <PlayerInfoIcon sx={{ marginRight: 1 }} />
              Player info
            </MenuItem>
            {game.canJoin && (
              <MenuItem
                onClick={async () => {
                  await handleJoinGame();
                  handleMenuClose();
                }}
                disabled={isSubmitting}
              >
                <JoinGameIcon sx={{ marginRight: 1 }} />
                Join game
              </MenuItem>
            )}
            {game.canLeave && (
              <MenuItem
                onClick={async () => {
                  await handleLeaveGame();
                  handleMenuClose();
                }}
                disabled={isSubmitting}
              >
                <LeaveGameIcon sx={{ marginRight: 1 }} />
                Leave game
              </MenuItem>
            )}
            <MenuItem
              onClick={() => {
                handleShare();
                handleMenuClose();
              }}
              disabled={isSubmitting}
            >
              <ShareIcon sx={{ marginRight: 1 }} />
              Share
            </MenuItem>
          </Menu>
        </>
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
          <Button
            sx={styles.avatarStackButton}
            onClick={() => {
              handleClickPlayerInfo(game.ID);
            }}
          >
            <Stack
              sx={styles.avatarStackContainer}
              direction="row"
              spacing={-1}
            >
              {game.Members.map((member, index) => (
                <Avatar
                  sx={styles.avatar}
                  key={index}
                  src={member.User.Picture}
                />
              ))}
            </Stack>
          </Button>
        </Stack>
      </Stack>
    </ListItem>
  );
};

export { GameCard };
