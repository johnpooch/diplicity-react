import React from "react";
import MyGames from "./pages/MyGames";
import CreateGame from "./pages/CreateGame";
import { Route, Routes } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import FindGames from "./pages/FindGames";
import PageWrapper from "./components/PageWrapper";
import GameCard from "./components/GameCard";

const defaultGame = {
  id: "1",
  title: "Game 1",
  users: [{ username: "User 1" }, { username: "User 2" }],
  onClickPlayerInfo: () => {},
  onClickGameInfo: () => {},
  onClickShare: () => {},
  onClickJoin: () => {},
  onClickLeave: () => {},
  link: "https://example.com",
  canJoin: false,
  canLeave: false,
  private: false,
  phaseDuration: "24h",
  variant: "Classical",
};

const games: React.ComponentProps<typeof GameCard>[] = [
  {
    ...defaultGame,
    status: "staging",
  },
  {
    ...defaultGame,
    status: "staging",
  },
  {
    ...defaultGame,
    status: "active",
  },
  {
    ...defaultGame,
    status: "active",
  },
  {
    ...defaultGame,
    status: "finished",
  },
  {
    ...defaultGame,
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
