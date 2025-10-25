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
import { feedbackActions, service } from "../store";

type Game = {
  id: string;
  canJoin: boolean;
  canLeave: boolean;
};

type GameMenuProps = {
  game: Game;
  onClickGameInfo: (navigate: NavigateFunction, gameId: string) => void;
  onClickPlayerInfo: (navigate: NavigateFunction, gameId: string) => void;
};

const GameMenu: React.FC<GameMenuProps> = props => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const [joinGame, joinGameQuery] =
    service.endpoints.gameJoinCreate.useMutation();

  const [leaveGame, leaveGameQuery] =
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
      feedbackActions.setFeedback({
        message: "Link copied to clipboard",
        severity: "success",
      })
    );
    handleMenuClose();
  };

  const handleClickJoinGame = async () => {
    await joinGame({ gameId: props.game.id, member: {} });
    handleMenuClose();
  };

  const handleClickLeaveGame = async () => {
    await leaveGame({ gameId: props.game.id });
    handleMenuClose();
  };

  return (
    <>
      <IconButton onClick={handleMenuOpen}>
        <MenuIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {props.game.canJoin && (
          <MenuItem
            onClick={handleClickJoinGame}
            disabled={joinGameQuery.isLoading}
          >
            <ListItem disablePadding>
              <ListItemIcon>
                <JoinGameIcon />
              </ListItemIcon>
              <ListItemText primary="Join game" />
            </ListItem>
          </MenuItem>
        )}
        {props.game.canLeave && (
          <MenuItem
            onClick={handleClickLeaveGame}
            disabled={leaveGameQuery.isLoading}
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
