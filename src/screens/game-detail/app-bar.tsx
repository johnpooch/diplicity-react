import { AppBar, Stack, IconButton } from "@mui/material";
import {
  ArrowBack as BackIcon,
  MoreHoriz as MenuIcon,
} from "@mui/icons-material";
import React from "react";
import { PhaseSelect } from "../../components/phase-select";

const GameDetailAppBar: React.FC = () => {
  return (
    <AppBar position="static" elevation={0}>
      <Stack sx={{ p: 1 }} direction="row" justifyContent="space-between">
        <IconButton edge="start" color="inherit">
          <BackIcon />
        </IconButton>
        <PhaseSelect />
        <IconButton edge="start" color="inherit">
          <MenuIcon />
        </IconButton>
      </Stack>
    </AppBar>
  );
};

export { GameDetailAppBar };
