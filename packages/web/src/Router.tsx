import React, { Suspense } from "react";
import {
  createBrowserRouter,
  Outlet,
  RouterProvider,
  redirect,
  useRouteError,
} from "react-router";
import { QueryClient } from "@tanstack/react-query";
import { Login } from "./screens/Login";
import { GameDetail, Home } from "./screens";
import { ErrorFallbackUI } from "./components/ErrorBoundary";
import { HomeLayout } from "./components/HomeLayout";
import { GameDetailLayout } from "./components/GameDetailLayout";
import { GamePhaseRedirect } from "./components/GamePhaseRedirect";
import { getVariantsListQueryOptions } from "./api/generated/endpoints";
import * as Sentry from "@sentry/react";

const RouteFallback: React.FC = () => (
  <div className="flex-1 flex items-center justify-center">
    <div className="animate-pulse text-muted-foreground"></div>
  </div>
);

const RootErrorBoundary: React.FC = () => {
  const error = useRouteError() as Error;

  React.useEffect(() => {
    if (error) {
      Sentry.captureException(error);
    }
  }, [error]);

  return <ErrorFallbackUI error={error} />;
};

const createVariantsLoader = (queryClient: QueryClient) => async () => {
  return queryClient.fetchQuery(getVariantsListQueryOptions());
};

const HomeLayoutWrapper: React.FC = () => {
  return (
    <HomeLayout>
      <Outlet />
    </HomeLayout>
  );
};

const GameDetailLayoutWrapper: React.FC = () => {
  return (
    <GameDetailLayout>
      <Outlet />
    </GameDetailLayout>
  );
};

const GameIndexRoute: React.FC = () => {
  const isMobile = window.innerWidth < 1024;
  return (
    <Suspense fallback={<RouteFallback />}>
      {isMobile ? <GameDetail.MapScreen /> : <GameDetail.OrdersScreen />}
    </Suspense>
  );
};

interface RouterProps {
  loggedIn: boolean;
  queryClient: QueryClient;
}

const Router: React.FC<RouterProps> = ({ loggedIn, queryClient }) => {
  const router = React.useMemo(
    () =>
      loggedIn
        ? createBrowserRouter([
            {
              id: "root",
              path: "/",
              errorElement: <RootErrorBoundary />,
              loader: createVariantsLoader(queryClient),
              children: [
                {
                  element: <HomeLayoutWrapper />,
                  children: [
                    {
                      index: true,
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.MyGames />
                        </Suspense>
                      ),
                    },
                    {
                      path: "find-games",
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.FindGames />
                        </Suspense>
                      ),
                    },
                    {
                      path: "create-game",
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.CreateGame />
                        </Suspense>
                      ),
                    },
                    {
                      path: "sandbox",
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.SandboxGames />
                        </Suspense>
                      ),
                    },
                    {
                      path: "profile",
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.Profile />
                        </Suspense>
                      ),
                    },
                    {
                      path: "game-info/:gameId",
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.GameInfoScreen />
                        </Suspense>
                      ),
                    },
                    {
                      path: "player-info/:gameId",
                      element: (
                        <Suspense fallback={<RouteFallback />}>
                          <Home.PlayerInfoScreen />
                        </Suspense>
                      ),
                    },
                  ],
                },
                {
                  path: "game/:gameId",
                  children: [
                    // Redirect /game/:gameId to /game/:gameId/phase/:currentPhaseId/orders
                    { index: true, element: <GamePhaseRedirect /> },
                    {
                      path: "phase/:phaseId",
                      element: <GameDetailLayoutWrapper />,
                      children: [
                        { index: true, element: <GameIndexRoute /> },
                        {
                          path: "orders",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.OrdersScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "chat",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.ChannelListScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "chat/channel/create",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.ChannelCreateScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "chat/channel/:channelId",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.ChannelScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "game-info",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.GameInfoScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "player-info",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.PlayerInfoScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "propose-draw",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.ProposeDrawScreen />
                            </Suspense>
                          ),
                        },
                        {
                          path: "draw-proposals",
                          element: (
                            <Suspense fallback={<RouteFallback />}>
                              <GameDetail.DrawProposalsScreen />
                            </Suspense>
                          ),
                        },
                      ],
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
    [loggedIn, queryClient]
  );

  return <RouterProvider router={router} />;
};

export default Router;
