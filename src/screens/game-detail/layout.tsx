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

const GameDetailLayout: React.FC = () => {
  const { gameId } = useParams();
  if (!gameId) throw new Error("No gameId found");
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [navigation, setNavigation] = useState(location.pathname);

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  const handleNavigationChange = (newValue: string) => {
    setNavigation(newValue);
    navigate(newValue);
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
                    key={item.value(gameId)}
                    label={item.label}
                    icon={item.icon}
                    value={item.value(gameId)}
                  />
                ))}
              </BottomNavigation>
            </AppBar>
          </>
        ) : (
          <Stack sx={styles.root}>
            <Outlet />
          </Stack>
        )}
      </SelectedPhaseContextProvider>
    </GameDetailContextProvider>
  );
};

export { GameDetailLayout };
