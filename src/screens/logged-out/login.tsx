import React from "react";
import { Button, Typography, Box, Stack } from "@mui/material";

const getLoginUrl = (): string => {
  const redirectUrl = location.href;
  const tokenDuration = 60 * 60 * 24 * 365 * 100;
  return `https://diplicity-engine.appspot.com/Auth/Login?redirect-to=${encodeURI(
    redirectUrl,
  )}&token-duration=${tokenDuration}`;
};

const Login: React.FC = () => {
  const onClickLogin = () => {
    const loginUrl = getLoginUrl();
    if (window) {
      window.open(loginUrl, "_self");
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      height="100vh"
      bgcolor="#f5f5f5"
      sx={{
        backgroundImage: "url('/src/static/img/login_background.jpg')", // Change to your image path
        backgroundSize: "cover",
        backgroundPosition: "54%",
        backgroundRepeat: "no-repeat",
      }}
    >
      <Stack
        sx={{
          minWidth: 300,
          padding: 2,
          bgcolor: "#f5f5f5",
          borderRadius: "4px",
        }}
        spacing={2}
        alignItems="center"
      >
        <img
          src="/otto.png"
          alt="Diplicity Logo"
          style={{ height: 48, width: 48 }}
        />
        <Typography variant="h1" component="div" align="left">
          Welcome to Diplicity!
        </Typography>
        <Typography variant="body1">
          A digital adaptation of the game of Diplomacy. Currently in Beta - not
          open for players yet.
        </Typography>
        <Box display="flex" justifyContent="center" mt={2}>
          <Button variant="contained" color="primary" onClick={onClickLogin}>
            Log in with Google
          </Button>
        </Box>
      </Stack>
    </Box>
  );
};

export { Login };
