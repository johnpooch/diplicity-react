import React from "react";
import MyGames from "./pages/MyGames";
import CreateGame from "./pages/CreateGame";
import { Route, Routes } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import FindGames from "./pages/FindGames";
import PageWrapper from "./components/PageWrapper";

const games = [
  {
    id: "1",
    title: "Game 1",
    users: [{ username: "User 1" }, { username: "User 2" }],
    onClickPlayerInfo: () => {},
    onClickGameInfo: () => {},
    onClickShare: () => {},
    link: "https://example.com",
    status: "staging",
  },
  {
    id: "1",
    title: "Game 1",
    users: [{ username: "User 1" }, { username: "User 2" }],
    onClickPlayerInfo: () => {},
    onClickGameInfo: () => {},
    onClickShare: () => {},
    link: "https://example.com",
    status: "staging",
  },
  {
    id: "1",
    title: "Game 1",
    users: [{ username: "User 1" }, { username: "User 2" }],
    onClickPlayerInfo: () => {},
    onClickGameInfo: () => {},
    onClickShare: () => {},
    link: "https://example.com",
    status: "active",
  },
  {
    id: "1",
    title: "Game 1",
    users: [{ username: "User 1" }, { username: "User 2" }],
    onClickPlayerInfo: () => {},
    onClickGameInfo: () => {},
    onClickShare: () => {},
    link: "https://example.com",
    status: "active",
  },
  {
    id: "1",
    title: "Game 1",
    users: [{ username: "User 1" }, { username: "User 2" }],
    onClickPlayerInfo: () => {},
    onClickGameInfo: () => {},
    onClickShare: () => {},
    link: "https://example.com",
    status: "finished",
  },
  {
    id: "1",
    title: "Game 1",
    users: [{ username: "User 1" }, { username: "User 2" }],
    onClickPlayerInfo: () => {},
    onClickGameInfo: () => {},
    onClickShare: () => {},
    link: "https://example.com",
    status: "finished",
  },
];

const Router: React.FC = () => {
  return (
    <Routes>
      <Route
        index
        element={
          <NavigationWrapper>
            <PageWrapper>
              <MyGames games={games} />
            </PageWrapper>
          </NavigationWrapper>
        }
      />
      <Route
        path="find-games"
        element={
          <NavigationWrapper>
            <PageWrapper>
              <FindGames games={games} />
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
    </Routes>
  );
};

export default Router;
