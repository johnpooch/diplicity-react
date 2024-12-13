import React, { useState } from "react";
import {
  Stack,
  Typography,
  Snackbar,
  Alert,
  TextField,
  MenuItem,
} from "@mui/material";
import GameCard from "../components/GameCard";
import GameCardSkeleton from "../components/GameCardSkeleton";

type Game = React.ComponentProps<typeof GameCard> & { link: string };

const FindGames: React.FC<{
  games: Game[];
}> = ({ games }) => {
  const [snackbar, setSnackbar] = useState<
    undefined | Pick<React.ComponentProps<typeof Alert>, "severity" | "title">
  >();

  const handleSnackbarClose = () => {
    setSnackbar(undefined);
  };

  return (
    <>
      <Stack>
        <Typography variant="h1">Find games</Typography>
        <Stack spacing={1} direction="row" style={{ paddingTop: 12 }}>
          {/* variant dropdown */}
          <TextField
            select
            label="Variant"
            variant="outlined"
            value={undefined}
            onChange={() => {}}
            size="small"
            style={{ width: 110 }}
          >
            <MenuItem value="Classical">Classical</MenuItem>
          </TextField>
          {/* deadline dropdown */}
          <TextField
            select
            label="Deadline"
            variant="outlined"
            value={undefined}
            onChange={() => {}}
            size="small"
            style={{ width: 110 }}
          >
            <MenuItem value="12">12 hours</MenuItem>
            <MenuItem value="24">24 hours</MenuItem>
            <MenuItem value="48">48 hours</MenuItem>
          </TextField>
        </Stack>
        <Stack spacing={1} style={{ paddingTop: 12 }}>
          {games.map((game) => (
            <GameCard
              key={game.id}
              users={game.users}
              title={game.title}
              status={game.status}
              id={game.id}
            />
          ))}
          <GameCardSkeleton />
        </Stack>
      </Stack>
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

export default FindGames;
