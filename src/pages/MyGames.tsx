import React, { useState } from "react";
import { Stack, Modal, Box, Typography, Snackbar, Alert } from "@mui/material";
import GameCard from "../components/GameCard";
import GameCardSkeleton from "../components/GameCardSkeleton";

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

const MyGames: React.FC<{
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

  games = games.map((game) => ({
    ...game,
    onClickPlayerInfo: () => onClickPlayerInfo(game),
    onClickGameInfo: () => onClickGameInfo(game),
    onClickShare: () => onClickShare(game.link),
  }));

  const stagingGames = games.filter((game) => game.status === "staging");
  const activeGames = games.filter((game) => game.status === "active");
  const finishedGames = games.filter((game) => game.status === "finished");

  return (
    <>
      <Stack>
        <Typography variant="h1">My games</Typography>
        <Stack spacing={2}>
          <div style={{ paddingTop: 24, paddingBottom: 24 }}>
            <Typography variant="h2">Staging Games</Typography>
            <Stack spacing={1} style={{ paddingTop: 12 }}>
              {stagingGames.map((game) => (
                <GameCard key={game.id} {...game} />
              ))}
              <GameCardSkeleton />
            </Stack>
          </div>
          <div style={{ paddingTop: 24, paddingBottom: 24 }}>
            <Typography variant="h2" style={{ paddingBottom: 12 }}>
              Active Games
            </Typography>
            <Stack spacing={1} style={{ paddingTop: 12 }}>
              {activeGames.map((game) => (
                <GameCard key={game.id} {...game} />
              ))}
              <GameCardSkeleton />
            </Stack>
          </div>
          <div style={{ paddingTop: 24, paddingBottom: 24 }}>
            <Typography variant="h2">Finished Games</Typography>
            <Stack spacing={1} style={{ paddingTop: 12 }}>
              {finishedGames.map((game) => (
                <GameCard key={game.id} {...game} />
              ))}
              <GameCardSkeleton />
            </Stack>
          </div>
        </Stack>
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

export default MyGames;