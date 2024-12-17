import React from "react";
import { Button } from "@mui/material";

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

  return <Button onClick={onClickLogin}>Log in</Button>;
};

export default Login;
