import React, { useState } from "react";
import { Stack, Typography, Snackbar, Alert, TextField } from "@mui/material";

const CreateGame: React.FC = () => {
  const [snackbar, setSnackbar] = useState<
    undefined | Pick<React.ComponentProps<typeof Alert>, "severity" | "title">
  >();

  const handleSnackbarClose = () => {
    setSnackbar(undefined);
  };

  return (
    <>
      <Stack>
        <Typography variant="h4" component="h1">
          Create Game
        </Typography>
        <Stack spacing={1}>
          <TextField label="Game Name" variant="outlined" value={""} />
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

export default CreateGame;
