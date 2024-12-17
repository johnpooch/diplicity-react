import React, { useState } from "react";
import {
  Stack,
  Typography,
  Snackbar,
  Alert,
  TextField,
  MenuItem,
} from "@mui/material";

const BrowseGamesScreen: React.FC = () => {
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
        {/* <>
                      <GameCard
                        key={game.id}
                        {...game}
                        {...props.gameCallbacks}
                      />
                      <Divider />
                    </> */}
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

export default BrowseGamesScreen;
