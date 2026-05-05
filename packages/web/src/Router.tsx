import React, { Suspense } from "react";
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouteObject,
  RouterProvider,
  useRouteError,
} from "react-router";
import { QueryClient } from "@tanstack/react-query";
import { Login } from "./screens/Login";
import { Register } from "./screens/Register";
import { CheckEmail } from "./screens/CheckEmail";
import { ForgotPassword } from "./screens/ForgotPassword";
import { VerifyEmail } from "./screens/VerifyEmail";
import { ResetPassword } from "./screens/ResetPassword";
import { GameDetail, Home } from "./screens";
import { ErrorFallbackUI } from "./components/ErrorBoundary";
import { HomeLayout } from "./components/HomeLayout";
import { GameDetailLayout } from "./components/GameDetailLayout";
import { GamePhaseRedirect } from "./components/GamePhaseRedirect";
import { getVariantsListQueryOptions } from "./api/generated/endpoints";
import * as Sentry from "@sentry/react";
import { useDeepLink } from "./deepLink";
import { useAuth } from "./auth";

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

const AppRoot: React.FC = () => {
  useDeepLink();
  return <Outlet />;
};

export const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loggedIn } = useAuth();
  if (!loggedIn) return <Navigate to="/login" />;
  return <>{children}</>;
};

export const RedirectIfAuthenticated: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loggedIn } = useAuth();
  if (loggedIn) return <Navigate to="/" replace />;
  return <>{children}</>;
};

export const ConditionalIndex: React.FC = () => {
  const { loggedIn } = useAuth();
  return loggedIn ? <Home.MyGames /> : <Home.FindGames />;
};

const GameIndexRoute: React.FC = () => {
  const isMobile = window.innerWidth < 1024;
  return (
    <Suspense fallback={<RouteFallback />}>
      {isMobile ? <GameDetail.MapScreen /> : <GameDetail.OrdersScreen />}
    </Suspense>
  );
};

export const routeObjects: RouteObject[] = [
  {
    id: "root",
    path: "/",
    element: <AppRoot />,
    errorElement: <RootErrorBoundary />,
    children: [
      {
        element: <HomeLayoutWrapper />,
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<RouteFallback />}>
                <ConditionalIndex />
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
              <RequireAuth>
                <Suspense fallback={<RouteFallback />}>
                  <Home.CreateGame />
                </Suspense>
              </RequireAuth>
            ),
          },
          {
            path: "profile",
            element: (
              <RequireAuth>
                <Suspense fallback={<RouteFallback />}>
                  <Home.Profile />
                </Suspense>
              </RequireAuth>
            ),
          },
          {
            path: "delete-account",
            element: (
              <RequireAuth>
                <Suspense fallback={<RouteFallback />}>
                  <Home.DeleteAccount />
                </Suspense>
              </RequireAuth>
            ),
          },
          {
            path: "community",
            element: (
              <Suspense fallback={<RouteFallback />}>
                <Home.Community />
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
                  <RequireAuth>
                    <Suspense fallback={<RouteFallback />}>
                      <GameDetail.ChannelCreateScreen />
                    </Suspense>
                  </RequireAuth>
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
                  <RequireAuth>
                    <Suspense fallback={<RouteFallback />}>
                      <GameDetail.ProposeDrawScreen />
                    </Suspense>
                  </RequireAuth>
                ),
              },
              {
                path: "draw-proposals",
                element: (
                  <RequireAuth>
                    <Suspense fallback={<RouteFallback />}>
                      <GameDetail.DrawProposalsScreen />
                    </Suspense>
                  </RequireAuth>
                ),
              },
            ],
          },
        ],
      },
      {
        path: "login",
        element: <RedirectIfAuthenticated><Login /></RedirectIfAuthenticated>,
      },
      {
        path: "register",
        element: <RedirectIfAuthenticated><Register /></RedirectIfAuthenticated>,
      },
      {
        path: "forgot-password",
        element: <RedirectIfAuthenticated><ForgotPassword /></RedirectIfAuthenticated>,
      },
      {
        path: "check-email",
        element: <RedirectIfAuthenticated><CheckEmail /></RedirectIfAuthenticated>,
      },
      {
        path: "verify-email",
        element: <RedirectIfAuthenticated><VerifyEmail /></RedirectIfAuthenticated>,
      },
      {
        path: "reset-password",
        element: <RedirectIfAuthenticated><ResetPassword /></RedirectIfAuthenticated>,
      },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
];

interface RouterProps {
  queryClient: QueryClient;
}

const Router: React.FC<RouterProps> = ({ queryClient }) => {
  const router = React.useMemo(() => {
    const routes = routeObjects.map(route => ({
      ...route,
      loader: route.id === "root" ? createVariantsLoader(queryClient) : undefined,
    }));
    return createBrowserRouter(routes);
  }, [queryClient]);

  return <RouterProvider router={router} />;
};

export default Router;
