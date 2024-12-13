import React from "react";
import MyGames from "./pages/MyGames";
import CreateGame from "./pages/CreateGame";
import { Route, Routes } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import FindGames from "./pages/FindGames";
import PageWrapper from "./components/PageWrapper";
import Login from "./pages/Login";
import { useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import { Stack } from "@mui/material";
import UserInfo from "./components/UserInfo";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);

  return loggedIn ? (
    <Routes>
      <Route
        index
        element={
          <NavigationWrapper>
            <PageWrapper>
              <Stack direction="row" gap={4}>
                <MyGames />
                <Stack style={{ minWidth: 320 }}>
                  <UserInfo />
                </Stack>
              </Stack>
            </PageWrapper>
          </NavigationWrapper>
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
    </Routes>
  ) : (
    <Routes>
      <Route index element={<Login />} />
    </Routes>
  );
};

export default Router;
