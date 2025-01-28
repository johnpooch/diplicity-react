import React from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router";
import Login from "./screens/Login";
import { useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import { Map } from "./components/Map";
import { GameDetailsLayout } from "./components/GameDetailsLayout";
import { GameDetailsNavigation } from "./components/GameDetailsNavigation";
import { Orders } from "./components/orders";
import { CreateOrderAction } from "./components/CreateOrderAction";
import { ConfirmOrdersAction } from "./components/ConfirmOrdersAction";
import {
  CreateGame,
  FindGames,
  GameInfo,
  Layout as HomeLayout,
  MyGames,
  PlayerInfo,
  Profile,
} from "./screens";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const navigate = useNavigate();

  const onClickCreateOrder = () => {
    const searchParams = new URLSearchParams(location.search);
    searchParams.set("createOrder", "true");
    navigate({ search: searchParams.toString() });
  };

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
      <Route path="game/:gameId">
        <Route
          element={
            <GameDetailsLayout
              onClickBack={() => navigate("/")}
              onClickCreateOrder={onClickCreateOrder}
              navigation={<GameDetailsNavigation />}
              actions={[<ConfirmOrdersAction />, <CreateOrderAction />]}
              modals={
                [
                  // <Modal name="createOrder">{() => <CreateOrder />}</Modal>,
                ]
              }
            />
          }
        >
          <Route index element={<Map />} />
          <Route path="orders" element={<Orders />} />
          <Route path="players" element={<div>Players</div>} />
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
