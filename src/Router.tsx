import React from "react";
import { HomeScreen } from "./screens/HomeScreen";
import CreateGame from "./screens/CreateGame";
import { Route, Routes } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import FindGames from "./screens/BrowseGamesScreen";
import PageWrapper from "./components/PageWrapper";
import Login from "./screens/Login";
import { useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import UserPage from "./screens/UserPage";
import { useHomeQuery } from "./common";
import { GameCallbacks } from "./components/GameCard";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);

  const gameCallbacks: GameCallbacks = {
    onClickPlayerInfo: (id) => console.log("onClickPlayerInfo", id),
    onClickGameInfo: (id) => console.log("onClickGameInfo", id),
    onClickShare: (id) => console.log("onClickShare", id),
    onClickJoin: (id) => console.log("onClickJoin", id),
    onClickLeave: (id) => console.log("onClickLeave", id),
  };

  return loggedIn ? (
    <Routes>
      <Route
        index
        element={
          <HomeScreen
            useHomeQuery={useHomeQuery}
            gameCallbacks={gameCallbacks}
          />
        }
      />
      <Route
        path="find-games"
        element={
          <NavigationWrapper>
            <PageWrapper>
              <FindGames />
            </PageWrapper>
          </NavigationWrapper>
        }
      />
      <Route
        path="create-game"
        element={
          <NavigationWrapper>
            <PageWrapper>
              <CreateGame />
            </PageWrapper>
          </NavigationWrapper>
        }
      />
      <Route
        path="user"
        element={
          <NavigationWrapper>
            <PageWrapper>
              <UserPage />
            </PageWrapper>
          </NavigationWrapper>
        }
      />
    </Routes>
  ) : (
    <Routes>
      <Route index element={<Login />} />
    </Routes>
  );
};

export default Router;
