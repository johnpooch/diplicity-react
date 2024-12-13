import React, { useState } from "react";
import MyGames from "./pages/MyGames";
import CreateGame from "./pages/CreateGame";
import { Route, Routes, useNavigate } from "react-router";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import {
  Home as HomeIcon,
  Search as SearchIcon,
  Add as AddIcon,
} from "@mui/icons-material";

type Navigation = "home" | "find-games" | "create-game";

const navigationPathMap: Record<Navigation, string> = {
  home: "/",
  "find-games": "/find-games",
  "create-game": "/create-game",
};

const Router: React.FC = () => {
  const [navigation, setNavigation] = useState<Navigation>("home");
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const navigate = useNavigate();

  return (
    <>
      <Routes>
        <Route
          index
          element={
            <MyGames
              games={[
                {
                  id: "1",
                  title: "Game 1",
                  users: [{ username: "User 1" }, { username: "User 2" }],
                  onClickPlayerInfo: () => {},
                  onClickGameInfo: () => {},
                  onClickShare: () => {},
                  link: "https://example.com",
                },
              ]}
            />
          }
        />
        <Route path="create-game" element={<CreateGame />} />
      </Routes>
      {isMobile && (
        <AppBar
          position="fixed"
          color="primary"
          sx={{ top: "auto", bottom: 0 }}
        >
          <BottomNavigation
            value={navigation}
            onChange={(event, newValue) => {
              setNavigation(newValue);
              navigate(navigationPathMap[newValue as Navigation]);
            }}
            showLabels
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
          </BottomNavigation>
        </AppBar>
      )}
    </>
  );
};

export default Router;
