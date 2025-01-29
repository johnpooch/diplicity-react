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
  Share as ShareIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router";
import { service } from "../common";

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

const GameCard: React.FC<{
  game: (typeof service.endpoints.listGames.Types.ResultType)[number];
}> = ({ game }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClickGame = () => {
    navigate(`/game/${game.ID}`);
  };

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.ID}`);
  };

  const handleClickPlayerInfo = (userId: string) => {
    navigate(`/player-info/${userId}`);
  };

  const handleClickShare = () => {
    navigator.clipboard.writeText(
      `${window.location.origin}/game-info/${game.ID}`
    );
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
            >
              <InfoIcon sx={{ marginRight: 1 }} />
              Game info
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleClickPlayerInfo(game.ID);
                handleMenuClose();
              }}
            >
              <PlayerInfoIcon sx={{ marginRight: 1 }} />
              Player info
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleClickShare();
                handleMenuClose();
              }}
            >
              <ShareIcon sx={{ marginRight: 1 }} />
              Share
            </MenuItem>
          </Menu>
        </>
      }
    >
      <Link
        href="#"
        underline="hover"
        onClick={() => {
          if (!game.Started) {
            handleClickGameInfo();
          } else {
            handleClickGame();
          }
        }}
      >
        <ListItemAvatar sx={styles.mapContainer}>
          <img
            src={`https://diplicity-engine.appspot.com/Variant/${game.Variant}/Map.svg`}
            alt={game.Variant}
          />
        </ListItemAvatar>
      </Link>
      <ListItemText
        primary={
          <Link
            href="#"
            underline="hover"
            onClick={() => {
              if (!game.Started) {
                handleClickGameInfo();
              } else {
                handleClickGame();
              }
            }}
          >
            <Typography>{game.Desc}</Typography>
          </Link>
        }
        secondary={
          <Stack sx={styles.secondaryContainer}>
            <Stack sx={styles.rulesContainer}>
              <Typography variant="caption">{game.Variant}</Typography>
              <Typography variant="caption">
                {game.PhaseLengthMinutes}
              </Typography>
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
  );
};

export { GameCard };
