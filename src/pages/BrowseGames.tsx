import React, { useState } from "react";
import {
  Stack,
  Modal,
  Box,
  Typography,
  Snackbar,
  Alert,
  AppBar,
  Toolbar,
  IconButton,
} from "@mui/material";
import { Menu as MenuIcon } from "@mui/icons-material";
import GameCard from "../components/GameCard";

const modalBoxStyle = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

type Game = React.ComponentProps<typeof GameCard> & { link: string };

const BrowseGames: React.FC<{
  games: Game[];
}> = ({ games }) => {
  const [openPlayerInfo, setOpenPlayerInfo] = useState(false);
  const [openGameInfo, setOpenGameInfo] = useState(false);
  const [selectedGame, setSelectedGame] = useState<Game | undefined>();

  const [snackbar, setSnackbar] = useState<
    undefined | Pick<React.ComponentProps<typeof Alert>, "severity" | "title">
  >();

  const handleOpenPlayerInfo = (game: Game) => {
    setSelectedGame(game);
    setOpenPlayerInfo(true);
  };

  const handleClosePlayerInfo = () => {
    setSelectedGame(undefined);
    setOpenPlayerInfo(false);
  };

  const handleOpenGameInfo = (game: Game) => {
    setSelectedGame(game);
    setOpenGameInfo(true);
  };

  const handleCloseGameInfo = () => {
    setSelectedGame(undefined);
    setOpenGameInfo(false);
  };

  const onClickPlayerInfo = (game: Game) => {
    handleOpenPlayerInfo(game);
  };

  const onClickGameInfo = (game: Game) => {
    handleOpenGameInfo(game);
  };

  const onClickShare = (link: string) => {
    navigator.clipboard.writeText(link).then(
      () => {
        setSnackbar({
          severity: "success",
          title: "Link copied to clipboard!",
        });
      },
      () => {
        setSnackbar({
          severity: "error",
          title: "Failed to copy link to clipboard!",
        });
      }
    );
  };

  const handleSnackbarClose = () => {
    setSnackbar(undefined);
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <IconButton edge="start" color="inherit" aria-label="menu">
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="h1">
            Browse Games
          </Typography>
        </Toolbar>
      </AppBar>
      <Stack spacing={1}>
        {games.map((game) => (
          <GameCard
            key={game.id}
            users={game.users}
            title={game.title}
            id={game.id}
            onClickPlayerInfo={() => onClickPlayerInfo(game)}
            onClickGameInfo={() => onClickGameInfo(game)}
            onClickShare={() => onClickShare(game.link)}
          />
        ))}
      </Stack>
      <Modal
        open={openPlayerInfo}
        onClose={handleClosePlayerInfo}
        aria-labelledby="player-info-modal-title"
        aria-describedby="player-info-modal-description"
      >
        <Box sx={modalBoxStyle}>
          {selectedGame && (
            <>
              <Typography
                id="player-info-modal-title"
                variant="h6"
                component="h2"
              >
                {selectedGame.title}
              </Typography>
              <Typography id="player-info-modal-description" sx={{ mt: 2 }}>
                Player info
              </Typography>
              <Stack spacing={1}>
                {selectedGame.users.map((user, index) => (
                  <Typography key={index}>{user.username}</Typography>
                ))}
              </Stack>
            </>
          )}
        </Box>
      </Modal>
      <Modal
        open={openGameInfo}
        onClose={handleCloseGameInfo}
        aria-labelledby="game-info-modal-title"
        aria-describedby="game-info-modal-description"
      >
        <Box sx={modalBoxStyle}>
          {selectedGame && (
            <>
              <Typography
                id="game-info-modal-title"
                variant="h6"
                component="h2"
              >
                {selectedGame.title}
              </Typography>
              <Typography id="game-info-modal-description" sx={{ mt: 2 }}>
                Game info content goes here.
              </Typography>
            </>
          )}
        </Box>
      </Modal>
      <Snackbar
        open={snackbar !== undefined}
        autoHideDuration={3000}
        onClose={handleSnackbarClose}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar?.severity}
          variant="filled"
          title={snackbar?.title}
        >
          {snackbar?.title}
        </Alert>
      </Snackbar>
    </>
  );
};

export default BrowseGames;
