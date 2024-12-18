import React from "react";
import { HomeScreen } from "./screens/HomeScreen";
import CreateGame from "./screens/CreateGame";
import { Route, Routes, useNavigate } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import { BrowseGamesScreen } from "./screens/BrowseGamesScreen";
import PageWrapper from "./components/PageWrapper";
import Login from "./screens/Login";
import { useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import UserPage from "./screens/UserPage";
import { GameCallbacks } from "./components/GameCard";
import { GameScreen } from "./screens/GameScreen";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const navigate = useNavigate();

  const gameCallbacks: GameCallbacks = {
    onClickPlayerInfo: (id) => console.log("onClickPlayerInfo", id),
    onClickGameInfo: (id) => console.log("onClickGameInfo", id),
    onClickShare: (id) => console.log("onClickShare", id),
    onClickJoin: (id) => console.log("onClickJoin", id),
    onClickLeave: (id) => console.log("onClickLeave", id),
    onClickViewGame: (id) => {
      navigate(`/game/${id}`);
    },
  };

  return loggedIn ? (
    <Routes>
      <Route index element={<HomeScreen gameCallbacks={gameCallbacks} />} />
      <Route
        path="find-games"
        element={<BrowseGamesScreen gameCallbacks={gameCallbacks} />}
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
      <Route path="game/:gameId" element={<GameScreen />} />
    </Routes>
  ) : (
    <Routes>
      <Route index element={<Login />} />
    </Routes>
  );
};

export default Router;
