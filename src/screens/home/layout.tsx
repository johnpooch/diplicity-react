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
  styled,
  Box,
} from "@mui/material";
import { Outlet, useLocation, useNavigate } from "react-router";
import {
  Home as MyGamesIcon,
  Search as FindGamesIcon,
  Add as CreateGameIcon,
  Person as ProfileIcon,
} from "@mui/icons-material";
import { DrawerNavigation, DrawerNavigationAction } from "../../components";

const NavigationItems = [
  { label: "My Games", icon: <MyGamesIcon />, value: "/" },
  { label: "Find Games", icon: <FindGamesIcon />, value: "/find-games" },
  { label: "Create Game", icon: <CreateGameIcon />, value: "/create-game" },
  { label: "Profile", icon: <ProfileIcon />, value: "/profile" },
] as const;

const ScreenContainer = styled(Box)(({ theme }) => ({
  height: "100%",
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
}));

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
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
          <AppBar
            position="fixed"
            color="primary"
            sx={{ top: "auto", bottom: 0 }}
          >
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
        <Stack alignItems="center">
          <Grid2
            container
            justifyContent="center"
            sx={{ maxWidth: 1000, width: "100%" }}
          >
            {/* Drawer navigation */}
            <Grid2
              size="auto"
              sx={{
                position: "sticky",
                top: 0,
                alignSelf: "flex-start",
                height: "100vh",
                overflow: "auto",
              }}
            >
              <DrawerNavigation
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
            {/* Main content */}
            <Grid2
              size="grow"
              sx={{ display: "flex", justifyContent: "center", flexGrow: 1 }}
            >
              <Grid2 sx={{ maxWidth: 600, width: "100%", minHeight: "100vh" }}>
                <ScreenContainer>
                  <Outlet />
                </ScreenContainer>
              </Grid2>
            </Grid2>
            {/* About panel */}
            <Grid2
              padding={2}
              size="auto"
              sx={{
                width: 240,
                position: "sticky",
                top: 0,
                alignSelf: "flex-start",
                height: "100vh",
                overflow: "auto",
              }}
            >
              <Stack spacing={1}>
                <Typography
                  variant="body1"
                  sx={{ fontWeight: 600, textAlign: "left" }}
                >
                  Welcome to Diplicity!
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ textAlign: "left" }}
                  color="textSecondary"
                >
                  If you're new to the game, you can learn more about it{" "}
                  <a
                    href="https://en.wikipedia.org/wiki/Diplomacy_(game)"
                    target="_blank"
                    rel="noreferrer"
                  >
                    here
                  </a>
                  .
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ textAlign: "left" }}
                  color="textSecondary"
                >
                  To chat with the developers or meet other players, join our{" "}
                  <a
                    href="https://discord.gg/9m7bJX4"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Discord server
                  </a>
                  .
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ textAlign: "left" }}
                  color="textSecondary"
                >
                  We massively appreciate your support and feedback! If you have
                  any questions or suggestions, please let us know by sending an{" "}
                  <a
                    href="mailto:diplicity.feedback@gmail.com"
                    target="_blank"
                    rel="noreferrer"
                  >
                    email
                  </a>
                  .
                </Typography>
              </Stack>
            </Grid2>
          </Grid2>
        </Stack>
      )}
    </>
  );
};

export { Layout };
