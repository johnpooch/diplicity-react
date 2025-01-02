import React from "react";
import { Button, Card, CardContent, Typography, Box } from "@mui/material";

const getLoginUrl = (): string => {
  const redirectUrl = location.href;
  const tokenDuration = 60 * 60 * 24;
  return `https://diplicity-engine.appspot.com/Auth/Login?redirect-to=${encodeURI(
    redirectUrl
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
    >
      <Card sx={{ minWidth: 300, padding: 2 }}>
        <CardContent>
          <Typography component="div" gutterBottom align="center">
            Welcome to Diplicity!
          </Typography>
          <Box display="flex" justifyContent="center" mt={2}>
            <Button variant="contained" color="primary" onClick={onClickLogin}>
              Log in
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Login;
