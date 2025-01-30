import React from "react";
import { Navigate, Route, Routes } from "react-router";
import Login from "./screens/Login";
import { useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import {
  CreateGame,
  FindGames,
  GameInfo,
  HomeLayout,
  GameDetailLayout,
  MyGames,
  PlayerInfo,
  Profile,
  Map,
  Orders,
  Chat,
} from "./screens";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);

  return loggedIn ? (
    <Routes>
      <Route element={<HomeLayout />}>
        <Route index element={<MyGames />} />
        <Route path="find-games" element={<FindGames />} />
        <Route path="create-game" element={<CreateGame />} />
        <Route path="profile" element={<Profile />} />
        <Route path="game-info/:gameId" element={<GameInfo />} />
        <Route path="player-info/:gameId" element={<PlayerInfo />} />
      </Route>
      <Route element={<GameDetailLayout />}>
        <Route path="game/:gameId">
          <Route index element={<Map />} />
          <Route path="orders" element={<Orders />} />
          <Route path="chat" element={<Chat />} />
          <Route path="game-info" element={<GameInfo />} />
          <Route path="player-info" element={<PlayerInfo />} />
        </Route>
      </Route>
    </Routes>
  ) : (
    <Routes>
      <Route path="*" element={<Navigate to="/" />} />
      <Route path="/" element={<Login />} />
    </Routes>
  );
};

export default Router;
