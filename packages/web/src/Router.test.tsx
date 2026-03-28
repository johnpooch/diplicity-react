import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const mockLoggedIn = vi.fn(() => false);

vi.mock("@/auth", () => ({
  useAuth: () => ({
    loggedIn: mockLoggedIn(),
    login: vi.fn(),
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGamesListSuspense: () => ({ data: [] }),
  useVariantsListSuspense: () => ({ data: [] }),
  useUserRetrieveSuspense: () => ({ data: { name: "Test", picture: null } }),
  useAuthEmailLoginCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useAuthLoginCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  getVariantsListQueryOptions: () => ({
    queryKey: ["variants"],
    queryFn: () => [],
  }),
}));

vi.mock("@/deepLink", () => ({
  useDeepLink: vi.fn(),
}));

vi.mock("@/utils/platform", () => ({
  isNativePlatform: () => false,
}));

vi.mock("@react-oauth/google", () => ({
  GoogleLogin: () => <div data-testid="google-login">Google Sign In</div>,
}));

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual("@tanstack/react-query");
  return {
    ...actual,
    QueryClient: vi.fn().mockImplementation(() => ({
      fetchQuery: vi.fn().mockResolvedValue([]),
    })),
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
    }),
  };
});

vi.mock("./screens", () => ({
  Home: {
    MyGames: () => <div data-testid="my-games-screen">My Games</div>,
    FindGames: () => <div data-testid="find-games-screen">Find Games</div>,
    CreateGame: () => <div data-testid="create-game-screen">Create Game</div>,
    SandboxGames: () => <div data-testid="sandbox-screen">Sandbox</div>,
    Profile: () => <div data-testid="profile-screen">Profile</div>,
    DeleteAccount: () => (
      <div data-testid="delete-account-screen">Delete Account</div>
    ),
    Community: () => <div data-testid="community-screen">Community</div>,
    GameInfoScreen: () => <div data-testid="game-info-screen">Game Info</div>,
    PlayerInfoScreen: () => (
      <div data-testid="player-info-screen">Player Info</div>
    ),
  },
  GameDetail: {
    MapScreen: () => <div data-testid="map-screen">Map</div>,
    OrdersScreen: () => <div data-testid="orders-screen">Orders</div>,
    ChannelListScreen: () => (
      <div data-testid="channel-list-screen">Channel List</div>
    ),
    ChannelCreateScreen: () => (
      <div data-testid="channel-create-screen">Channel Create</div>
    ),
    ChannelScreen: () => <div data-testid="channel-screen">Channel</div>,
    GameInfoScreen: () => (
      <div data-testid="game-detail-info-screen">Game Info</div>
    ),
    PlayerInfoScreen: () => (
      <div data-testid="game-detail-player-info-screen">Player Info</div>
    ),
    ProposeDrawScreen: () => (
      <div data-testid="propose-draw-screen">Propose Draw</div>
    ),
    DrawProposalsScreen: () => (
      <div data-testid="draw-proposals-screen">Draw Proposals</div>
    ),
  },
}));

import { routeObjects } from "./Router";

const renderRoute = (initialPath: string) => {
  const router = createMemoryRouter(routeObjects, {
    initialEntries: [initialPath],
  });
  return render(<RouterProvider router={router} />);
};

describe("Router", () => {
  describe("when user is not logged in", () => {
    it("redirects auth-required routes to /login", async () => {
      mockLoggedIn.mockReturnValue(false);
      renderRoute("/create-game");

      expect(
        await screen.findByRole("button", { name: /sign in/i })
      ).toBeInTheDocument();
    });

    it("can access /find-games without auth", async () => {
      mockLoggedIn.mockReturnValue(false);
      renderRoute("/find-games");

      expect(
        await screen.findByTestId("find-games-screen")
      ).toBeInTheDocument();
    });

    it("shows FindGames at / for anonymous users", async () => {
      mockLoggedIn.mockReturnValue(false);
      renderRoute("/");

      expect(
        await screen.findByTestId("find-games-screen")
      ).toBeInTheDocument();
    });
  });

  describe("when user is logged in", () => {
    it("shows MyGames at / for logged-in users", async () => {
      mockLoggedIn.mockReturnValue(true);
      renderRoute("/");

      expect(await screen.findByTestId("my-games-screen")).toBeInTheDocument();
    });

    it("redirects /login to /", async () => {
      mockLoggedIn.mockReturnValue(true);
      renderRoute("/login");

      expect(await screen.findByTestId("my-games-screen")).toBeInTheDocument();
    });

    it("can access auth-required routes when logged in", async () => {
      mockLoggedIn.mockReturnValue(true);
      renderRoute("/create-game");

      expect(
        await screen.findByTestId("create-game-screen")
      ).toBeInTheDocument();
    });
  });

  describe("auth-required routes redirect to /login when not logged in", () => {
    const authRoutes = [
      "/create-game",
      "/sandbox",
      "/profile",
      "/delete-account",
    ];

    authRoutes.forEach(route => {
      it(`${route} redirects to /login`, async () => {
        mockLoggedIn.mockReturnValue(false);
        renderRoute(route);

        expect(
          await screen.findByRole("button", { name: /sign in/i })
        ).toBeInTheDocument();
      });
    });
  });

  describe("public routes are accessible without auth", () => {
    const publicRoutes = [
      { path: "/find-games", testId: "find-games-screen" },
      { path: "/community", testId: "community-screen" },
    ];

    publicRoutes.forEach(({ path, testId }) => {
      it(`${path} is accessible`, async () => {
        mockLoggedIn.mockReturnValue(false);
        renderRoute(path);

        expect(await screen.findByTestId(testId)).toBeInTheDocument();
      });
    });
  });
});
