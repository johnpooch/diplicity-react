import React from "react";
import { Typography, Box, Stack, Avatar } from "@mui/material";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { service } from "../../store";

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
  const [trigger] = service.useAuthLoginCreateMutation();

  const handleLoginSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      console.error("No credential response received");
      return;
    }
    trigger({
      loginRequest: {
        id_token: credentialResponse.credential,
      },
    });
  };

  const handleLoginError = () => {
    console.error("Login failed");
  };

  return (
    <Box sx={styles.background}>
      <Stack sx={styles.stack} spacing={2} alignItems="center">
        <Avatar sx={styles.logo} src="/otto.png" alt="Diplicity Logo" />
        <Typography component="h1" variant="body1">
          Welcome to Diplicity! Hello world
        </Typography>
        <Typography variant="body2">
          A digital adaptation of the game of Diplomacy.
        </Typography>
        <Typography variant="caption">
          We're rebuilding the app. Currently not ready for players.
        </Typography>
        <Box sx={styles.buttonContainer}>
          <GoogleLogin
            onSuccess={handleLoginSuccess}
            onError={handleLoginError}
          />
        </Box>
      </Stack>
    </Box>
  );
};

export { Login };
