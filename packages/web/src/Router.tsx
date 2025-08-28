import React from "react";
import { Navigate, Outlet, Route, Routes } from "react-router";
import { useSelector } from "react-redux";
import { Login } from "./components/screens/Login";
import { MyGames as NewMyGames } from "./components/screens/MyGames";
import { FindGames as NewFindGames } from "./components/screens/FindGames";
import { CreateGame as NewCreateGame } from "./components/screens/CreateGame";
import { Profile as NewProfile } from "./components/screens/Profile";
import { GameInfo as NewGameInfo } from "./components/screens/GameInfo";
import { PlayerInfo as NewPlayerInfo } from "./components/screens/PlayerInfo";
import { selectAuth } from "./store";
import { SelectedGameContextProvider, SelectedPhaseContextProvider } from "./context";
import { GameDetail } from "./components/screens";
import { ChannelCreateScreen } from "./components/screens/GameDetail/ChannelCreateScreen";
import { ChannelScreen } from "./components/screens/GameDetail/ChannelScreen";
import { useResponsiveness } from "./components/utils/responsive";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const responsiveness = useResponsiveness();

  return loggedIn ? (
    <Routes>
      <Route index element={<NewMyGames />} />
      <Route path="/find-games" element={<NewFindGames />} />
      <Route path="/create-game" element={<NewCreateGame />} />
      <Route path="/profile" element={<NewProfile />} />
      <Route path="/game-info/:gameId" element={<NewGameInfo />} />
      <Route path="/player-info/:gameId" element={<NewPlayerInfo />} />
      <Route path="/game/:gameId" element={
        <SelectedGameContextProvider>
          <SelectedPhaseContextProvider>
            <Outlet />
          </SelectedPhaseContextProvider>
        </SelectedGameContextProvider>
      }>
        <Route
          path=""
          element={responsiveness.device === "mobile" ? <GameDetail.MapScreen /> : <GameDetail.OrdersScreen />}
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
          element={<ChannelCreateScreen />}
        />
        <Route
          path="chat/channel/:channelId"
          element={<ChannelScreen />}
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
