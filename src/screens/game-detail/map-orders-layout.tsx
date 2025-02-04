import React, { useEffect, useState } from "react";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  IconButton,
  Stack,
} from "@mui/material";
import {
  Map as MapIcon,
  Chat as ChatIcon,
  Gavel as OrdersIcon,
  ArrowBack as BackIcon,
} from "@mui/icons-material";
import { Outlet, useLocation, useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";
import { PhaseSelect } from "../../components/phase-select";
import { GameDetailMenu } from "./game-detail-menu";

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
  header: {
    padding: "8px 16px",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
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

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  return (
    <>
      <AppBar position="static" elevation={0}>
        <Stack sx={styles.header}>
          <IconButton edge="start" color="inherit" onClick={handleBack}>
            <BackIcon />
          </IconButton>
          <PhaseSelect />
          <GameDetailMenu />
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
