import React from "react";
import MyGames from "./pages/MyGames";
import CreateGame from "./pages/CreateGame";
import { Route, Routes } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import FindGames from "./pages/FindGames";

const Router: React.FC = () => {
  return (
    <Routes>
      <Route
        index
        element={
          <NavigationWrapper>
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
          </NavigationWrapper>
        }
      />
      <Route
        path="find-games"
        element={
          <NavigationWrapper>
            <FindGames />
          </NavigationWrapper>
        }
      />
      <Route
        path="create-game"
        element={
          <NavigationWrapper>
            <CreateGame />
          </NavigationWrapper>
        }
      />
    </Routes>
  );
};

export default Router;
