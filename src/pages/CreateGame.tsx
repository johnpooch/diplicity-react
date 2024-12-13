import React, { useState } from "react";
import {
  Stack,
  Typography,
  Snackbar,
  Alert,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
} from "@mui/material";

const CreateGame: React.FC = () => {
  const [snackbar, setSnackbar] = useState<
    undefined | Pick<React.ComponentProps<typeof Alert>, "severity" | "title">
  >();
  const [name, setName] = useState("");
  const [variant, setVariant] = useState("Classical");
  const [isPrivate, setIsPrivate] = useState(false);

  const handleSnackbarClose = () => {
    setSnackbar(undefined);
  };

  const handleCreateGame = () => {
    // Logic to create the game goes here
    setSnackbar({ severity: "success", title: "Game created successfully!" });
  };

  return (
    <>
      <Stack spacing={2}>
        <Typography variant="h1">Create Game</Typography>
        <TextField
          label="Game Name"
          variant="outlined"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextField
          select
          label="Variant"
          variant="outlined"
          value={variant}
          onChange={(e) => setVariant(e.target.value)}
        >
          <MenuItem value="Classical">Classical</MenuItem>
        </TextField>
        <FormControlLabel
          control={
            <Checkbox
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
            />
          }
          label="Private"
        />
        <Button variant="contained" color="primary" onClick={handleCreateGame}>
          Create
        </Button>
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
        >
          {snackbar?.title}
        </Alert>
      </Snackbar>
    </>
  );
};

export default CreateGame;
