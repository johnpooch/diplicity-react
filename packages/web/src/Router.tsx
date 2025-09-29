import React from "react";
import { Navigate, Outlet, Route, Routes } from "react-router";
import { useSelector } from "react-redux";
import { Login } from "./screens/Login";
import { selectAuth } from "./store";
import { SelectedGameContextProvider, SelectedPhaseContextProvider } from "./context";
import { GameDetail, Home } from "./screens";
import { useResponsiveness } from "./components/utils/responsive";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const responsiveness = useResponsiveness();

  return loggedIn ? (
    <Routes>
      <Route index element={<Home.MyGames />} />
      <Route path="/find-games" element={<Home.FindGames />} />
      <Route path="/create-game" element={<Home.CreateGame />} />
      <Route path="/profile" element={<Home.Profile />} />
      <Route path="/game-info/:gameId" element={<Home.GameInfo />} />
      <Route path="/player-info/:gameId" element={<Home.PlayerInfo />} />
      <Route path="/game/:gameId" element={
        <SelectedGameContextProvider>
          <SelectedPhaseContextProvider>
            <Outlet />
          </SelectedPhaseContextProvider>
        </SelectedGameContextProvider>
      }>
        <Route
          path=""
          element={responsiveness.device !== "desktop" ? <GameDetail.MapScreen /> : <GameDetail.OrdersScreen />}
        />
        <Route
          path="game-info"
          element={<GameDetail.GameInfoScreen />}
        />
        <Route
          path="player-info"
          element={<GameDetail.PlayerInfoScreen />}
        />
        <Route
          path="orders"
          element={<GameDetail.OrdersScreen />}
        />
        <Route
          path="chat"
          element={<GameDetail.ChannelListScreen />}
        />
        <Route
          path="chat/channel/create"
          element={<GameDetail.ChannelCreateScreen />}
        />
        <Route
          path="chat/channel/:channelId"
          element={<GameDetail.ChannelScreen />}
        />
      </Route>
    </Routes >
  ) : (
    <Routes>
      <Route path="*" element={<Navigate to="/" />} />
      <Route path="/" element={<Login />} />
    </Routes>
  );
};

export default Router;
