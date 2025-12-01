import React from "react";
import {
  createBrowserRouter,
  Outlet,
  RouterProvider,
  redirect,
  useRouteError,
} from "react-router";
import { Login } from "./screens/Login";
import {
  SelectedGameContextProvider,
  SelectedPhaseContextProvider,
} from "./context";
import { GameDetail, Home } from "./screens";
import { store } from "./store";
import { service } from "./store/service";
import { ErrorFallbackUI } from "./components/ErrorBoundary";
import * as Sentry from "@sentry/react";

const RootErrorBoundary: React.FC = () => {
  const error = useRouteError() as Error;

  React.useEffect(() => {
    if (error) {
      Sentry.captureException(error);
    }
  }, [error]);

  return <ErrorFallbackUI error={error} />;
};

const variantsLoader = async () => {
  const result = await store.dispatch(
    service.endpoints.variantsList.initiate()
  );
  return result.data || [];
};

const AuthLayout: React.FC = () => {
  return <Outlet />;
};

const GameInfoLayout: React.FC = () => {
  return (
    <SelectedGameContextProvider>
      <Outlet />
    </SelectedGameContextProvider>
  );
};

const GameLayout: React.FC = () => {
  return (
    <SelectedGameContextProvider>
      <SelectedPhaseContextProvider>
        <Outlet />
      </SelectedPhaseContextProvider>
    </SelectedGameContextProvider>
  );
};

const GameIndexRoute: React.FC = () => {
  const isMobile = window.innerWidth < 1024;
  return isMobile ? <GameDetail.MapScreen /> : <GameDetail.OrdersScreen />;
};

interface RouterProps {
  loggedIn: boolean;
}

const Router: React.FC<RouterProps> = ({ loggedIn }) => {
  const router = React.useMemo(
    () =>
      loggedIn
        ? createBrowserRouter([
            {
              id: "root",
              path: "/",
              element: <AuthLayout />,
              errorElement: <RootErrorBoundary />,
              loader: variantsLoader,
              children: [
                {
                  index: true,
                  element: <Home.MyGames />,
                },
                {
                  path: "find-games",
                  element: <Home.FindGames />,
                },
                {
                  path: "create-game",
                  element: <Home.CreateGame />,
                },
                {
                  path: "sandbox",
                  element: <Home.SandboxGames />,
                },
                {
                  path: "profile",
                  element: <Home.Profile />,
                },
                {
                  path: "game-info/:gameId",
                  element: <GameInfoLayout />,
                  children: [
                    {
                      index: true,
                      element: <Home.GameInfo />,
                    },
                  ],
                },
                {
                  path: "player-info/:gameId",
                  element: <Home.PlayerInfo />,
                },
                {
                  path: "game/:gameId",
                  element: <GameLayout />,
                  children: [
                    {
                      index: true,
                      element: <GameIndexRoute />,
                    },
                    {
                      path: "game-info",
                      element: <GameDetail.GameInfoScreen />,
                    },
                    {
                      path: "player-info",
                      element: <GameDetail.PlayerInfoScreen />,
                    },
                    {
                      path: "orders",
                      element: <GameDetail.OrdersScreen />,
                    },
                    {
                      path: "chat",
                      element: <GameDetail.ChannelListScreen />,
                    },
                    {
                      path: "chat/channel/create",
                      element: <GameDetail.ChannelCreateScreen />,
                    },
                    {
                      path: "chat/channel/:channelId",
                      element: <GameDetail.ChannelScreen />,
                    },
                  ],
                },
              ],
            },
          ])
        : createBrowserRouter([
            {
              path: "/",
              element: <Login />,
            },
            {
              path: "*",
              loader: () => redirect("/"),
            },
          ]),
    [loggedIn]
  );

  return <RouterProvider router={router} />;
};

export default Router;
