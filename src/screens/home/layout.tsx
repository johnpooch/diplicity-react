import React, { useState, useEffect } from "react";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  useTheme,
  useMediaQuery,
  Grid2,
  Stack,
  Typography,
  Link,
} from "@mui/material";
import { Outlet, useLocation, useNavigate } from "react-router";
import {
  Home as MyGamesIcon,
  Search as FindGamesIcon,
  Add as CreateGameIcon,
  Person as ProfileIcon,
} from "@mui/icons-material";
import { DrawerNavigation, DrawerNavigationAction } from "../../components";

const styles: Styles = {
  mobileAppBar: {
    top: "auto",
    bottom: 0,
  },
  drawerNavigationContainer: {
    position: "sticky",
    top: 0,
    alignSelf: "flex-start",
    overflow: "auto",
  },
  largeRoot: {
    alignItems: "center",
  },
  largeContentContainer: {
    display: "flex",
    justifyContent: "center",
    flexGrow: 1,
    maxWidth: 1000,
    width: "100%",
  },
  contentContainer: (theme) => ({
    width: "100%",
    maxWidth: 600,
    minHeight: "100vh",
    height: "100%",
    border: `1px solid ${theme.palette.divider}`,
  }),
  infoContainer: {
    width: 240,
    position: "sticky",
    padding: 2,
    top: 0,
    alignSelf: "flex-start",
    height: "100vh",
    overflow: "auto",
    gap: 1,
  },
  infoTitle: {
    fontWeight: 600,
  },
};

const NavigationItems = [
  { label: "My Games", icon: <MyGamesIcon />, value: "/" },
  { label: "Find Games", icon: <FindGamesIcon />, value: "/find-games" },
  { label: "Create Game", icon: <CreateGameIcon />, value: "/create-game" },
  { label: "Profile", icon: <ProfileIcon />, value: "/profile" },
] as const;

const InfoPanel: React.FC = () => {
  const learnLink =
    "https://diplicity.notion.site/Diplicity-FAQ-7b4e0a119eb54c69b80b411f14d43bb9";
  const discordLink =
    "https://discord.com/channels/565625522407604254/697344626859704340";

  return (
    <Stack sx={styles.infoContainer}>
      <Typography variant="body1" sx={styles.infoTitle}>
        Welcome to Diplicity!
      </Typography>
      <Typography variant="body2" color="textSecondary">
        If you're new to the game, read our{" "}
        <Link href={learnLink} target="_blank" rel="noreferrer">
          FAQ
        </Link>
        .
      </Typography>
      <Typography variant="body2" color="textSecondary">
        To chat with the developers or meet other players, join our{" "}
        <Link href={discordLink} target="_blank" rel="noreferrer">
          Discord community
        </Link>
        .
      </Typography>
    </Stack>
  );
};

const HomeLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [navigation, setNavigation] = useState(location.pathname);

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  const handleNavigationChange = (newValue: string) => {
    setNavigation(newValue);
    navigate(newValue);
  };

  return (
    <>
      {isMobile ? (
        <>
          <Outlet />
          <Stack sx={{ height: 56 }} />
          <AppBar position="fixed" color="primary" sx={styles.mobileAppBar}>
            <BottomNavigation
              value={navigation}
              onChange={(_event, newValue) => handleNavigationChange(newValue)}
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
        <Stack sx={styles.largeRoot}>
          <Grid2 container sx={styles.largeContentContainer}>
            <Grid2 size="auto" sx={styles.drawerNavigationContainer}>
              <DrawerNavigation
                variant={isDesktop ? "expanded" : "collapsed"}
                value={navigation}
                onChange={handleNavigationChange}
              >
                {NavigationItems.map((item) => (
                  <DrawerNavigationAction
                    key={item.value}
                    label={item.label}
                    icon={item.icon}
                    value={item.value}
                  />
                ))}
              </DrawerNavigation>
            </Grid2>
            <Grid2 size="grow">
              <Stack sx={{ alignItems: "center" }}>
                <Stack sx={styles.contentContainer}>
                  <Outlet />
                </Stack>
              </Stack>
            </Grid2>
            {isDesktop && <InfoPanel />}
          </Grid2>
        </Stack>
      )}
    </>
  );
};

export { HomeLayout };
