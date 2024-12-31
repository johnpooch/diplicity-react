import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  useTheme,
  useMediaQuery,
  List,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  ListItem,
  Stack,
  Avatar,
} from "@mui/material";
import {
  Home as HomeIcon,
  Search as SearchIcon,
  Add as AddIcon,
} from "@mui/icons-material";
import service from "../common/store/service";

type Navigation = "home" | "find-games" | "create-game" | "user";

const navigationPathMap: Record<Navigation, string> = {
  home: "/",
  "find-games": "/find-games",
  "create-game": "/create-game",
  user: "/user",
};

const TabletNavigation: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return <List style={{ width: "fit-content" }}>{children}</List>;
};

const DesktopNavigation: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return <List style={{ width: "220px" }}>{children}</List>;
};

const TabletNavigationAction: React.FC<{
  label: string;
  icon: React.ReactElement;
  path: string;
  style?: React.CSSProperties;
}> = ({ label, icon, path, style }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const selectedItemIconStyle = {
    color: theme.palette.common.black,
  };

  return (
    <ListItem disablePadding sx={{ display: "block" }}>
      <ListItemButton onClick={() => navigate(path)} style={{ padding: 16 }}>
        <ListItemIcon style={{ minWidth: 0 }} aria-label={label}>
          {React.cloneElement(icon, {
            style:
              location.pathname === path
                ? { ...style, ...selectedItemIconStyle }
                : { ...style },
          })}
        </ListItemIcon>
      </ListItemButton>
    </ListItem>
  );
};

const DesktopNavigationAction: React.FC<{
  label: string;
  icon: React.ReactElement;
  path: string;
  style?: React.CSSProperties;
}> = ({ label, icon, path, style }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const selectedItemIconStyle = {
    color: theme.palette.common.black,
  };

  const selectedItemTextStyle = {
    color: theme.palette.common.black,
    fontWeight: "bold",
  };

  return (
    <ListItem disablePadding sx={{ display: "block" }}>
      <ListItemButton onClick={() => navigate(path)} style={{ padding: 16 }}>
        <ListItemIcon style={{ minWidth: 0 }}>
          {React.cloneElement(icon, {
            style:
              location.pathname === path
                ? { ...style, ...selectedItemIconStyle }
                : { ...style },
          })}
        </ListItemIcon>
        <ListItemText
          primary={label}
          sx={{ pl: 2, textAlign: "left" }}
          slotProps={{
            primary: {
              style: location.pathname === path ? selectedItemTextStyle : {},
            },
          }}
        />
      </ListItemButton>
    </ListItem>
  );
};

const NavigationWrapper: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [navigation, setNavigation] = useState<Navigation>("home");
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isTablet = useMediaQuery(theme.breakpoints.between("sm", "md"));
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const navigate = useNavigate();
  const rootQuery = service.endpoints.getRoot.useQuery(undefined);

  return isMobile ? (
    <>
      {children}
      <AppBar position="fixed" color="primary" sx={{ top: "auto", bottom: 0 }}>
        <BottomNavigation
          value={navigation}
          onChange={(_event, newValue) => {
            setNavigation(newValue);
            navigate(navigationPathMap[newValue as Navigation]);
          }}
        >
          <BottomNavigationAction
            label="Home"
            icon={<HomeIcon />}
            value="home"
          />
          <BottomNavigationAction
            label="Find Games"
            icon={<SearchIcon />}
            value="find-games"
          />
          <BottomNavigationAction
            label="Create Game"
            icon={<AddIcon />}
            value="create-game"
          />
          {rootQuery.isLoading ? (
            <BottomNavigationAction label="Loading..." icon={<Avatar />} />
          ) : (
            <BottomNavigationAction
              label="Profile"
              icon={<Avatar src={rootQuery.data?.Picture} />}
              value="user"
            />
          )}
        </BottomNavigation>
      </AppBar>
    </>
  ) : isTablet ? (
    <Stack direction="row" spacing={2}>
      <TabletNavigation>
        <TabletNavigationAction label="Home" icon={<HomeIcon />} path="/" />
        <TabletNavigationAction
          label="Find Games"
          icon={<SearchIcon />}
          path="/find-games"
        />
        <TabletNavigationAction
          label="Create Game"
          icon={<AddIcon />}
          path="/create-game"
        />
        {rootQuery.isLoading ? (
          <TabletNavigationAction
            label="Loading..."
            path="/user"
            icon={<Avatar style={{ width: 24, height: 24 }} />}
          />
        ) : (
          <TabletNavigationAction
            label="User"
            icon={<Avatar src={rootQuery.data?.Picture} />}
            style={{ width: 26, height: 26 }}
            path="/user"
          />
        )}
      </TabletNavigation>
      {children}
    </Stack>
  ) : isDesktop ? (
    <Stack direction="row" spacing={2} style={{ padding: 8 }}>
      <DesktopNavigation>
        <DesktopNavigationAction label="Home" icon={<HomeIcon />} path="/" />
        <DesktopNavigationAction
          label="Find Games"
          icon={<SearchIcon />}
          path="/find-games"
        />
        <DesktopNavigationAction
          label="Create Game"
          icon={<AddIcon />}
          path="/create-game"
        />
        {rootQuery.isLoading ? (
          <DesktopNavigationAction
            label="Loading..."
            path="/user"
            icon={<Avatar style={{ width: 24, height: 24 }} />}
          />
        ) : (
          <DesktopNavigationAction
            label="Profile"
            icon={<Avatar src={rootQuery.data?.Picture} />}
            style={{ width: 26, height: 26 }}
            path="/user"
          />
        )}
      </DesktopNavigation>
      {children}
    </Stack>
  ) : (
    <div>Not implemented</div>
  );
};

export default NavigationWrapper;
