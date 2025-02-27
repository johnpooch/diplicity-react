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
  Toolbar,
  Avatar,
  Menu,
  MenuItem,
} from "@mui/material";
import { Outlet, useLocation, useNavigate } from "react-router";
import {
  Home as MyGamesIcon,
  Search as FindGamesIcon,
  Add as CreateGameIcon,
  Person as ProfileIcon,
} from "@mui/icons-material";
import { DrawerNavigation, DrawerNavigationAction } from "../../components";
import { service, actions } from "../../common";
import { useDispatch } from "react-redux";

const styles: Styles = {
  mobileAppBar: {
    top: "auto",
    bottom: 0,
  },
  drawerNavigationContainer: {
    position: "sticky",
    top: "64px",
    alignSelf: "flex-start",
    overflow: "auto",
    display: "flex",                 
    flexShrink: 0,                  
  },
  largeContentContainer: {
    display: "flex",
    justifyContent: "center",
    flexGrow: 1,
    maxWidth: 1000,
    width: "100%",
    minHeight: "100vh", 
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
  topAppBar: {
    backgroundColor: 'background.paper',
    borderBottom: 1,
    borderColor: 'divider',
  },
  contentContainer: (theme) => ({
    width: "100%",
    maxWidth: 600,
    minHeight: "calc(100vh - 56px)", 
    height: "100%",
    border: `1px solid ${theme.palette.divider}`,
  }),
  toolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  avatar: {
    border: '1px solid black',
    height: 40,
    width: 40,
  },
  infoContainer: {
    width: 240,
    position: "sticky",
    padding: 2,
    top: "64px",
    alignSelf: "flex-start",
    height: "100vh",
    overflow: "auto",
    gap: 1,
  },
  infoTitle: {
    fontWeight: 'bold',
    mb: 1,
  },
};
const NavigationItems = [
  { label: "My Games", icon: <MyGamesIcon />, value: "/" },
  { label: "Find Games", icon: <FindGamesIcon />, value: "/find-games" },
  { label: "Create Game", icon: <CreateGameIcon />, value: "/create-game" },
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
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [navigation, setNavigation] = useState(location.pathname);
  const rootQuery = service.endpoints.getRoot.useQuery(undefined);

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  const handleNavigationChange = (newValue: string) => {
    setNavigation(newValue);
    navigate(newValue);
  };
  // Add these state handlers near the other state declarations in HomeLayout
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  const handleLogout = () => {
    dispatch(actions.logout());
    handleMenuClose();
  };
  return (
    <>
      <AppBar position="fixed" elevation={3} sx={styles.topAppBar}>
        <Toolbar sx={styles.toolbar}>
          <Stack sx={styles.logoContainer}>
            <img
              src="/otto.png"
              alt="Diplicity"
              style={{ height: 32, width: 32 }}
            />
            <Typography variant="h6">Diplicity</Typography>
          </Stack>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ cursor: 'pointer' }} onClick={handleMenuClick}>
            {!isMobile && <Typography variant="body1">{rootQuery.data?.Name}</Typography>}
            <Avatar 
              src={rootQuery.data?.Picture} 
              alt={rootQuery.data?.Name}
              sx={styles.avatar}
            />
          </Stack>
          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            {isMobile && (
              <MenuItem sx={{ pointerEvents: 'none', opacity: 0.7 }}>
                {rootQuery.data?.Name}
              </MenuItem>
            )}
            <MenuItem onClick={handleLogout}>Logout</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Toolbar /> {/* This creates space for the fixed AppBar */}
      
      {isMobile ? (
        <>
          <Outlet />
          <Stack sx={{ height: 56 }} />
          <AppBar position="fixed" color="primary" sx={styles.mobileAppBar}>
            <BottomNavigation
              value={navigation}
              onChange={(_event, newValue) => handleNavigationChange(newValue)}
            >
              {NavigationItems.filter(item => item.value !== '/create-game').map((item) => (
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
