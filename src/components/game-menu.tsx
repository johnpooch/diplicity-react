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
import { NavigateFunction, useLocation, useNavigate } from "react-router";
import { JoinLeaveButton } from "./game-join-leave-button";
import { useDispatch } from "react-redux";
import { actions } from "../common";

type GameMenuProps = {
  gameId: string;
  onClickGameInfo: (navigate: NavigateFunction, gameId: string) => void;
  onClickPlayerInfo: (navigate: NavigateFunction, gameId: string) => void;
};

const GameMenu: React.FC<GameMenuProps> = (props) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClickGameInfo = () => {
    props.onClickGameInfo(navigate, props.gameId);
    handleMenuClose();
  };

  const handleClickPlayerInfo = () => {
    props.onClickPlayerInfo(navigate, props.gameId);
    handleMenuClose();
  };

  const handleClickShare = () => {
    navigator.clipboard.writeText(
      `${window.location.origin}${location.pathname}`
    );
    dispatch(
      actions.setFeedback({
        message: "Link copied to clipboard",
        severity: "success",
      })
    );
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
        <JoinLeaveButton gameId={props.gameId} onJoinLeave={handleMenuClose} />
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

export { GameMenu };
