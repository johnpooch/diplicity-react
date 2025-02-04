import React from "react";
import { Navigate, Route, Routes } from "react-router";
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
  Channel,
  CreateChannel,
  MapOrdersLayout,
  GameDetail,
  ChannelList,
  Login,
} from "./screens";
import { ChannelLayout } from "./screens/game-detail/channel-layout";
import { useMediaQuery, useTheme } from "@mui/material";
import { ChannelListLayout } from "./screens/game-detail/channel-list-layout";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

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
      {isMobile ? (
        <Route element={<GameDetailLayout />}>
          <Route
            path="game/:gameId/chat/create-channel"
            element={<CreateChannel />}
          />
          <Route
            path="game/:gameId/chat/channel/:channelName"
            element={<ChannelLayout />}
          >
            <Route index element={<Channel />} />
          </Route>
          <Route path="game/:gameId/chat">
            <Route element={<ChannelListLayout />}>
              <Route index element={<ChannelList />} />
            </Route>
          </Route>
          <Route path="game/:gameId/player-info">
            <Route index element={<PlayerInfo />} />
          </Route>
          <Route path="game/:gameId/game-info">
            <Route index element={<GameInfo />} />
          </Route>
          <Route path="game/:gameId">
            <Route element={<MapOrdersLayout />}>
              <Route index element={<Map />} />
              <Route path="orders" element={<Orders />} />
            </Route>
          </Route>
        </Route>
      ) : (
        <>
          <Route element={<GameDetailLayout />}>
            <Route
              path="game/:gameId/chat/channel/:channelName"
              element={<ChannelLayout />}
            >
              <Route index element={<GameDetail />} />
            </Route>
            <Route path="game/:gameId">
              <Route index element={<GameDetail />} />
              <Route path="*" element={<GameDetail />} />
            </Route>
          </Route>
        </>
      )}
    </Routes>
  ) : (
    <Routes>
      <Route path="*" element={<Navigate to="/" />} />
      <Route path="/" element={<Login />} />
    </Routes>
  );
};

export default Router;
