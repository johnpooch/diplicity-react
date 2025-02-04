import React, { useEffect, useState } from "react";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Stack,
} from "@mui/material";
import {
  Map as MapIcon,
  Chat as ChatIcon,
  Gavel as OrdersIcon,
  ArrowBack as BackIcon,
  MoreHoriz as MenuIcon,
  Info as InfoIcon,
  Person as PlayerInfoIcon,
  Share as ShareIcon,
} from "@mui/icons-material";
import { Outlet, useLocation, useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";
import { PhaseSelect } from "../../components/phase-select";

const styles: Styles = {
  mobileAppBar: {
    top: "auto",
    bottom: 0,
  },
  fab: {
    position: "fixed",
    top: 16,
    left: 16,
  },
  root: {
    alignItems: "center",
  },
  contentContainer: {
    display: "flex",
    justifyContent: "center",
    flexGrow: 1,
    maxWidth: 1000,
    width: "100%",
  },
};

const NavigationItems = [
  {
    label: "Map",
    icon: <MapIcon />,
    value: (gameId: string) => `/game/${gameId}`,
  },
  {
    label: "Orders",
    icon: <OrdersIcon />,
    value: (gameId: string) => `/game/${gameId}/orders`,
  },
  {
    label: "Chat",
    icon: <ChatIcon />,
    value: (gameId: string) => `/game/${gameId}/chat`,
  },
] as const;

const MapOrdersLayout: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  const location = useLocation();
  const [navigation, setNavigation] = useState(location.pathname);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  const handleNavigationChange = (newValue: string) => {
    setNavigation(newValue);
    navigate(newValue);
  };

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

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  return (
    <>
      <AppBar position="static" elevation={0}>
        <Stack
          sx={{
            paddingLeft: 2,
            paddingRight: 2,
            paddingTop: 1,
            paddingBottom: 1,
          }}
          direction="row"
          justifyContent="space-between"
        >
          <Stack direction="row" alignItems="center" gap={1}>
            <IconButton edge="start" color="inherit" onClick={handleBack}>
              <BackIcon />
            </IconButton>
            <PhaseSelect />
          </Stack>
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
            <Divider />
            <MenuItem onClick={handleClickShare}>
              <ShareIcon sx={{ marginRight: 1 }} />
              Share
            </MenuItem>
          </Menu>
        </Stack>
      </AppBar>
      <Outlet />
      <AppBar position="fixed" color="primary" sx={styles.mobileAppBar}>
        <BottomNavigation
          value={navigation}
          onChange={(_event, newValue) => handleNavigationChange(newValue)}
        >
          {NavigationItems.map((item) => (
            <BottomNavigationAction
              key={item.value(gameId)}
              label={item.label}
              icon={item.icon}
              value={item.value(gameId)}
            />
          ))}
        </BottomNavigation>
      </AppBar>
    </>
  );
};

export { MapOrdersLayout };
