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
  Add as JoinGameIcon,
  Remove as LeaveGameIcon,
} from "@mui/icons-material";
import { useState } from "react";
import { NavigateFunction, useLocation, useNavigate } from "react-router";
import { useDispatch } from "react-redux";
import { actions } from "../common";
import { service } from "../store";

type GameMenuProps = {
  game: (typeof service.endpoints.gamesList.Types.ResultType)[number];
  onClickGameInfo: (navigate: NavigateFunction, gameId: number) => void;
  onClickPlayerInfo: (navigate: NavigateFunction, gameId: number) => void;
};

const GameMenu: React.FC<GameMenuProps> = (props) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const [joinGame, joinGameMutation] =
    service.endpoints.gameJoinCreate.useMutation();

  const [leaveGame, leaveGameMutation] =
    service.endpoints.gameLeaveDestroy.useMutation();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleClickGameInfo = () => {
    props.onClickGameInfo(navigate, props.game.id);
    handleMenuClose();
  };

  const handleClickPlayerInfo = () => {
    props.onClickPlayerInfo(navigate, props.game.id);
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

  const handleClickJoinGame = async () => {
    await joinGame({ gameId: props.game.id });
    handleMenuClose();
  };

  const handleClickLeaveGame = async () => {
    await leaveGame({ gameId: props.game.id });
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
        {props.game.actions.canJoin && (
          <MenuItem
            onClick={handleClickJoinGame}
            disabled={joinGameMutation.isLoading}
          >
            <ListItem disablePadding>
              <ListItemIcon>
                <JoinGameIcon />
              </ListItemIcon>
              <ListItemText primary="Join game" />
            </ListItem>
          </MenuItem>
        )}
        {props.game.actions.canLeave && (
          <MenuItem
            onClick={handleClickLeaveGame}
            disabled={leaveGameMutation.isLoading}
          >
            <ListItem disablePadding>
              <ListItemIcon>
                <LeaveGameIcon />
              </ListItemIcon>
              <ListItemText primary="Leave game" />
            </ListItem>
          </MenuItem>
        )}
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

export { GameMenu };
