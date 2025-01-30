import { AppBar, Stack, IconButton, Menu, MenuItem } from "@mui/material";
import {
  ArrowBack as BackIcon,
  MoreHoriz as MenuIcon,
  Info as InfoIcon,
  Person as PlayerInfoIcon,
  Share as ShareIcon,
} from "@mui/icons-material";
import React, { useState } from "react";
import { PhaseSelect } from "../../components/phase-select";
import { useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";

const GameDetailAppBar: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleBack = () => {
    navigate("/");
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClickGameInfo = () => {
    navigate(`/game/${gameId}/game-info`);
    handleMenuClose();
  };

  const handleClickPlayerInfo = () => {
    navigate(`/game/${gameId}/player-info`);
    handleMenuClose();
  };

  const handleClickShare = () => {
    navigator.clipboard.writeText(`${window.location.origin}/game/${gameId}`);
    handleMenuClose();
  };

  return (
    <AppBar position="static" elevation={0}>
      <Stack sx={{ p: 1 }} direction="row" justifyContent="space-between">
        <IconButton edge="start" color="inherit" onClick={handleBack}>
          <BackIcon />
        </IconButton>
        <PhaseSelect />
        <IconButton edge="start" color="inherit" onClick={handleMenuOpen}>
          <MenuIcon />
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleClickGameInfo}>
            <InfoIcon sx={{ marginRight: 1 }} />
            Game info
          </MenuItem>
          <MenuItem onClick={handleClickPlayerInfo}>
            <PlayerInfoIcon sx={{ marginRight: 1 }} />
            Player info
          </MenuItem>
          <MenuItem onClick={handleClickShare}>
            <ShareIcon sx={{ marginRight: 1 }} />
            Share
          </MenuItem>
        </Menu>
      </Stack>
    </AppBar>
  );
};

export { GameDetailAppBar };
