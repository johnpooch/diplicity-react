import React from "react";
import { HomeScreen } from "./screens/HomeScreen";
import CreateGame from "./screens/CreateGame";
import { Route, Routes, useNavigate } from "react-router";
import NavigationWrapper from "./components/NavigationWrapper";
import { BrowseGamesScreen } from "./screens/BrowseGamesScreen";
import PageWrapper from "./components/PageWrapper";
import Login from "./screens/Login";
import { useDispatch, useSelector } from "react-redux";
import { selectAuth } from "./common/store/auth";
import UserPage from "./screens/UserPage";
import { GameCallbacks } from "./components/GameCard";
import { GameScreen } from "./screens/GameScreen";
import service from "./common/store/service";
import { feedbackActions } from "./common/store/feedback";

const Router: React.FC = () => {
  const { loggedIn } = useSelector(selectAuth);
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
  const [leaveGameMutationTrigger] = service.endpoints.leaveGame.useMutation();
  const [joinGameMutationTrigger] = service.endpoints.joinGame.useMutation();

  const gameCallbacks: GameCallbacks = {
    onClickPlayerInfo: (id) => console.log("onClickPlayerInfo", id),
    onClickGameInfo: (id) => console.log("onClickGameInfo", id),
    onClickShare: (id) => console.log("onClickShare", id),
    onClickJoin: async (id) => {
      try {
        await joinGameMutationTrigger({
          gameId: id,
          NationPreferences: "",
          GameAlias: "",
        });
        navigate(`/`);
        dispatch(
          feedbackActions.setFeedback({
            message: "Joined game",
            severity: "success",
          })
        );
      } catch {
        dispatch(
          feedbackActions.setFeedback({
            message: "Could not join game",
            severity: "error",
          })
        );
      }
    },
    onClickLeave: async (id) => {
      if (!getRootQuery.data?.Id) return;
      try {
        await leaveGameMutationTrigger({
          gameId: id,
          userId: getRootQuery.data?.Id,
        });
        dispatch(
          feedbackActions.setFeedback({
            message: "Left game",
            severity: "success",
          })
        );
      } catch {
        dispatch(
          feedbackActions.setFeedback({
            message: "Could not leave game",
            severity: "error",
          })
        );
      }
    },
    onClickViewGame: (id) => {
      navigate(`/game/${id}`);
    },
  };

  const onClickBack = () => {
    navigate(-1);
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
      <Route path="game/:gameId">
        <Route index element={<GameScreen onClickBack={onClickBack} />} />
      </Route>
    </Routes>
  ) : (
    <Routes>
      <Route index element={<Login />} />
    </Routes>
  );
};

export default Router;
