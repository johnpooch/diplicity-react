import React, { useEffect, useState } from "react";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Stack,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import {
  Map as MapIcon,
  Chat as ChatIcon,
  Gavel as OrdersIcon,
} from "@mui/icons-material";
import { Outlet, useNavigate, useParams } from "react-router";
import {
  GameDetailContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";

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
  contentContainerMobile: {
    p: 1,
  },
  contentContainerLarge: {
    p: 4,
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
  { label: "Map", icon: <MapIcon />, value: "/" },
  { label: "Orders", icon: <OrdersIcon />, value: "/orders" },
  { label: "Chat", icon: <ChatIcon />, value: "/chat" },
] as const;

const GameDetailLayout: React.FC = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("No gameId found");
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const contentContainerStyle = isMobile
    ? styles.contentContainerMobile
    : styles.contentContainerLarge;
  const [navigation, setNavigation] = useState(location.pathname);

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  const handleNavigationChange = (newValue: string) => {
    const path = `/game/${gameId}${newValue}`;
    setNavigation(newValue);
    navigate(path);
  };

  return (
    <GameDetailContextProvider>
      <SelectedPhaseContextProvider>
        {isMobile ? (
          <>
            <Outlet />
            <AppBar position="fixed" color="primary" sx={styles.mobileAppBar}>
              <BottomNavigation
                value={navigation}
                onChange={(_event, newValue) =>
                  handleNavigationChange(newValue)
                }
              >
                {NavigationItems.map((item) => (
                  <BottomNavigationAction
                    key={item.value}
                    label={item.label}
                    icon={item.icon}
                    value={item.value}
                  />
                ))}
              </BottomNavigation>
            </AppBar>
          </>
        ) : (
          <Stack sx={styles.root}>
            <Stack
              sx={() => ({
                ...styles.contentContainer,
                ...contentContainerStyle,
              })}
            >
              <Outlet />
            </Stack>
          </Stack>
        )}
      </SelectedPhaseContextProvider>
    </GameDetailContextProvider>
  );
};

export { GameDetailLayout };
