import {
  Menu,
  MenuItem,
  Divider,
  IconButton,
  ListItem,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import {
  MoreHoriz as MenuIcon,
  Info as InfoIcon,
  Person as PlayerInfoIcon,
  Share as ShareIcon,
} from "@mui/icons-material";
import { useState } from "react";
import { useNavigate } from "react-router";
import { useGameDetailContext } from "../context";

const GameDetailMenu: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

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
    <>
      <IconButton edge="start" color="inherit" onClick={handleMenuOpen}>
        <MenuIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleClickGameInfo}>
          <ListItem disablePadding>
            <ListItemIcon>
              <InfoIcon />
            </ListItemIcon>
            <ListItemText primary="Game info" />
          </ListItem>
        </MenuItem>
        <MenuItem onClick={handleClickPlayerInfo}>
          <ListItem disablePadding>
            <ListItemIcon>
              <PlayerInfoIcon />
            </ListItemIcon>
            <ListItemText primary="Player info" />
          </ListItem>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleClickShare}>
          <ListItem disablePadding>
            <ListItemIcon>
              <ShareIcon />
            </ListItemIcon>
            <ListItemText primary="Share" />
          </ListItem>
        </MenuItem>
      </Menu>
    </>
  );
};

export { GameDetailMenu };
