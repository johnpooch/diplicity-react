import React from "react";

import { Typography, Stack } from "@mui/material";
import PageWrapper from "../components/PageWrapper";

const GameScreen: React.FC = () => {
  return (
    <PageWrapper>
      <Stack>
        <Typography variant="h1">Game screen</Typography>
      </Stack>
    </PageWrapper>
  );
};

export { GameScreen };
