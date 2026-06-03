import React, { Suspense } from "react";
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouterProvider,
  redirect,
  useLocation,
  useRouteError,
} from "react-router";
import { QueryClient } from "@tanstack/react-query";
import { Login } from "./screens/Login";
import { Register } from "./screens/Register";
import { CheckEmail } from "./screens/CheckEmail";
import { ForgotPassword } from "./screens/ForgotPassword";
import { VerifyEmail } from "./screens/VerifyEmail";
import { ResetPassword } from "./screens/ResetPassword";
import { GameDetail, Home, Variants } from "./screens";
import { ErrorFallbackUI } from "./components/ErrorBoundary";
import { HomeLayout } from "./components/HomeLayout";
import { GameDetailLayout } from "./components/GameDetailLayout";
import { GamePhaseRedirect } from "./components/GamePhaseRedirect";
import { getVariantsListQueryOptions } from "./api/generated/endpoints";
import * as Sentry from "@sentry/react";
import { deepLinkStorage, useDeepLink } from "./deepLink";
import { useIsMobile } from "./hooks/use-mobile";

const AuthContext = React.createContext(false);

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const loggedIn = React.useContext(AuthContext);
  const location = useLocation();
  if (!loggedIn) {
    const path = `${location.pathname}${location.search}${location.hash}`;
    if (location.pathname !== "/") {
      deepLinkStorage.setPendingPath(path);
    }
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const GuestOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const loggedIn = React.useContext(AuthContext);
  if (loggedIn) return <Navigate to="/" replace />;
  return <>{children}</>;
};

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

const AuthenticatedRoot: React.FC = () => {
  const loggedIn = React.useContext(AuthContext);
  useDeepLink(loggedIn);
  return <Outlet />;
};

const RootIndex: React.FC = () => {
  const loggedIn = React.useContext(AuthContext);
  if (!loggedIn) return <Login />;
  return (
    <Suspense fallback={<RouteFallback />}>
      <Home.MyGames />
    </Suspense>
  );
};

const GameIndexRoute: React.FC = () => {
  const isMobile = useIsMobile();
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
      createBrowserRouter([
        {
          id: "root",
          path: "/",
          element: <AuthenticatedRoot />,
          errorElement: <RootErrorBoundary />,
          loader: createVariantsLoader(queryClient),
          children: [
            {
              element: <HomeLayoutWrapper />,
              children: [
                {
                  index: true,
                  element: <RootIndex />,
                },
                {
                  path: "find-games",
                  element: (
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Home.FindGames />
                      </Suspense>
                    </RequireAuth>
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
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Home.Community />
                      </Suspense>
                    </RequireAuth>
                  ),
                },
                {
                  path: "learn-to-play",
                  element: (
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Home.LearnToPlay />
                      </Suspense>
                    </RequireAuth>
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
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Home.PlayerInfoScreen />
                      </Suspense>
                    </RequireAuth>
                  ),
                },
                {
                  path: "variants",
                  element: (
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Variants.VariantsList />
                      </Suspense>
                    </RequireAuth>
                  ),
                },
                {
                  path: "variants/create",
                  element: (
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Variants.VariantCreate />
                      </Suspense>
                    </RequireAuth>
                  ),
                },
                {
                  path: "variants/:variantId/edit",
                  element: (
                    <RequireAuth>
                      <Suspense fallback={<RouteFallback />}>
                        <Variants.VariantEditRoute />
                      </Suspense>
                    </RequireAuth>
                  ),
                },
              ],
            },
            {
              path: "register",
              element: (
                <GuestOnly>
                  <Register />
                </GuestOnly>
              ),
            },
            {
              path: "forgot-password",
              element: (
                <GuestOnly>
                  <ForgotPassword />
                </GuestOnly>
              ),
            },
            {
              path: "check-email",
              element: (
                <GuestOnly>
                  <CheckEmail />
                </GuestOnly>
              ),
            },
            {
              path: "verify-email",
              element: (
                <GuestOnly>
                  <VerifyEmail />
                </GuestOnly>
              ),
            },
            {
              path: "reset-password",
              element: (
                <GuestOnly>
                  <ResetPassword />
                </GuestOnly>
              ),
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
                        <RequireAuth>
                          <Suspense fallback={<RouteFallback />}>
                            <GameDetail.ChannelListScreen />
                          </Suspense>
                        </RequireAuth>
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
                        <RequireAuth>
                          <Suspense fallback={<RouteFallback />}>
                            <GameDetail.ChannelScreen />
                          </Suspense>
                        </RequireAuth>
                      ),
                    },
                    {
                      path: "game-info",
                      element: (
                        <RequireAuth>
                          <Suspense fallback={<RouteFallback />}>
                            <GameDetail.GameInfoScreen />
                          </Suspense>
                        </RequireAuth>
                      ),
                    },
                    {
                      path: "player-info",
                      element: (
                        <RequireAuth>
                          <Suspense fallback={<RouteFallback />}>
                            <GameDetail.PlayerInfoScreen />
                          </Suspense>
                        </RequireAuth>
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
              path: "*",
              loader: ({ request }) => {
                const url = new URL(request.url);
                const path = `${url.pathname}${url.search}${url.hash}`;
                if (url.pathname !== "/") {
                  deepLinkStorage.setPendingPath(path);
                }
                return redirect("/");
              },
            },
          ],
        },
      ]),
    [queryClient]
  );

  return (
    <AuthContext value={loggedIn}>
      <RouterProvider router={router} />
    </AuthContext>
  );
};

export default Router;
