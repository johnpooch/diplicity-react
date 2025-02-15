import React from "react";
import { Button, Typography, Box, Stack, Avatar } from "@mui/material";

const getLoginUrl = (): string => {
  const redirectUrl = location.href;
  const tokenDuration = 60 * 60 * 24 * 365 * 100;
  return `https://diplicity-engine.appspot.com/Auth/Login?redirect-to=${encodeURI(
    redirectUrl
  )}&token-duration=${tokenDuration}`;
};

const styles: Styles = {
  background: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundImage: "url('/src/static/img/login_background.jpg')",
    backgroundSize: "cover",
    backgroundPosition: "54%",
    backgroundRepeat: "no-repeat",
  },
  stack: (theme) => ({
    padding: 4,
    bgcolor: theme.palette.background.paper,
    borderRadius: "4px",
  }),
  logo: {
    height: 48,
    width: 48,
  },
  title: {
    variant: "h1",
    component: "div",
    align: "left",
  },
  subtitle: {
    variant: "body1",
  },
  buttonContainer: {
    display: "flex",
    justifyContent: "center",
    mt: 2,
  },
};

const Login: React.FC = () => {
  const onClickLogin = () => {
    const loginUrl = getLoginUrl();
    if (window) {
      window.open(loginUrl, "_self");
    }
  };

  return (
    <Box sx={styles.background}>
      <Stack sx={styles.stack} spacing={2} alignItems="center">
        <Avatar sx={styles.logo} src="/otto.png" alt="Diplicity Logo" />
        <Typography component="h1" variant="body1">
          Welcome to Diplicity!
        </Typography>
        <Typography variant="body2">
          A digital adaptation of the game of Diplomacy.
        </Typography>
        <Typography variant="caption">
          We're rebuilding the app. Currently not ready for players.
        </Typography>
        <Box sx={styles.buttonContainer}>
          <Button variant="contained" color="primary" onClick={onClickLogin}>
            Log in with Google
          </Button>
        </Box>
      </Stack>
    </Box>
  );
};

export { Login };
