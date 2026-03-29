import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";

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

vi.mock("./screens/Login", () => ({
  Login: () => <div data-testid="login-screen">Sign In</div>,
}));

vi.mock("./screens/Register", () => ({
  Register: () => <div>Register</div>,
}));
vi.mock("./screens/CheckEmail", () => ({
  CheckEmail: () => <div>Check Email</div>,
}));
vi.mock("./screens/ForgotPassword", () => ({
  ForgotPassword: () => <div>Forgot Password</div>,
}));
vi.mock("./screens/VerifyEmail", () => ({
  VerifyEmail: () => <div>Verify Email</div>,
}));
vi.mock("./screens/ResetPassword", () => ({
  ResetPassword: () => <div>Reset Password</div>,
}));

vi.mock("./screens", () => ({
  Home: {
    MyGames: () => <div data-testid="my-games-screen">My Games</div>,
    FindGames: () => <div data-testid="find-games-screen">Find Games</div>,
    CreateGame: () => <div>Create Game</div>,
    SandboxGames: () => <div>Sandbox</div>,
    Profile: () => <div>Profile</div>,
    DeleteAccount: () => <div>Delete Account</div>,
    Community: () => <div>Community</div>,
    GameInfoScreen: () => <div>Game Info</div>,
    PlayerInfoScreen: () => <div>Player Info</div>,
  },
  GameDetail: {
    MapScreen: () => <div>Map</div>,
    OrdersScreen: () => <div>Orders</div>,
    ChannelListScreen: () => <div>Channel List</div>,
    ChannelCreateScreen: () => <div>Channel Create</div>,
    ChannelScreen: () => <div>Channel</div>,
    GameInfoScreen: () => <div>Game Info</div>,
    PlayerInfoScreen: () => <div>Player Info</div>,
    ProposeDrawScreen: () => <div>Propose Draw</div>,
    DrawProposalsScreen: () => <div>Draw Proposals</div>,
  },
}));

vi.mock("./components/ErrorBoundary", () => ({
  ErrorFallbackUI: () => <div>Error</div>,
}));

vi.mock("./components/HomeLayout", () => ({
  HomeLayout: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock("./components/GameDetailLayout", () => ({
  GameDetailLayout: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock("./components/GamePhaseRedirect", () => ({
  GamePhaseRedirect: () => <div>Game Phase Redirect</div>,
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

vi.mock("@sentry/react", () => ({
  captureException: vi.fn(),
}));

import { RequireAuth, RedirectIfAuthenticated, ConditionalIndex } from "./Router";

const LoginScreen = () => <div data-testid="login-screen">Sign In</div>;
const ProtectedScreen = () => (
  <div data-testid="protected-screen">Protected</div>
);
const MyGamesScreen = () => <div data-testid="my-games-screen">My Games</div>;

describe("RequireAuth", () => {
  it("renders children when logged in", () => {
    mockLoggedIn.mockReturnValue(true);
    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <RequireAuth>
                <ProtectedScreen />
              </RequireAuth>
            }
          />
          <Route path="/login" element={<LoginScreen />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId("protected-screen")).toBeInTheDocument();
  });

  it("redirects to /login when not logged in", () => {
    mockLoggedIn.mockReturnValue(false);
    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <RequireAuth>
                <ProtectedScreen />
              </RequireAuth>
            }
          />
          <Route path="/login" element={<LoginScreen />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId("login-screen")).toBeInTheDocument();
    expect(screen.queryByTestId("protected-screen")).not.toBeInTheDocument();
  });
});

describe("RedirectIfAuthenticated", () => {
  it("renders children when logged out", () => {
    mockLoggedIn.mockReturnValue(false);
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route
            path="/login"
            element={
              <RedirectIfAuthenticated>
                <LoginScreen />
              </RedirectIfAuthenticated>
            }
          />
          <Route path="/" element={<MyGamesScreen />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId("login-screen")).toBeInTheDocument();
  });

  it("redirects to / when logged in", () => {
    mockLoggedIn.mockReturnValue(true);
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route
            path="/login"
            element={
              <RedirectIfAuthenticated>
                <LoginScreen />
              </RedirectIfAuthenticated>
            }
          />
          <Route path="/" element={<MyGamesScreen />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId("my-games-screen")).toBeInTheDocument();
    expect(screen.queryByTestId("login-screen")).not.toBeInTheDocument();
  });
});

describe("ConditionalIndex", () => {
  it("shows FindGames for anonymous users", () => {
    mockLoggedIn.mockReturnValue(false);
    render(
      <MemoryRouter>
        <ConditionalIndex />
      </MemoryRouter>
    );

    expect(screen.getByTestId("find-games-screen")).toBeInTheDocument();
  });

  it("shows MyGames for logged-in users", () => {
    mockLoggedIn.mockReturnValue(true);
    render(
      <MemoryRouter>
        <ConditionalIndex />
      </MemoryRouter>
    );

    expect(screen.getByTestId("my-games-screen")).toBeInTheDocument();
  });
});
